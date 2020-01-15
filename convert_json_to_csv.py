import os
import csv
from pprint import pprint
import argparse
import json
import yaml

# CORE_FIELDS = ['id', 'name', 'category', 'createdAt', \
# 			   'dataUpdatedAt', 'dataUri', 'description', 'domain', 'license', 'tags']

# CUSTOM_FIELDS = ['Data Governance__System of Record', 'Data Governance__Update Frequency', \
# 				 'Data Governance__Department', 'Data Governance__Team', 'Data Governance__Data Owner', \
# 				 'Data Governance__Data Steward', 'Data Governance__Vetted by Data Owner']

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", help="required: set metadata updates")
parser.add_argument("-o", "--output", help="required: Provide path to output file for CSV")
parser.add_argument("-c", "--config", help="required: provide path to metadata configuration yaml file")
args = parser.parse_args()


def load_metadata_config():
    metadata_config = {}
    try:
        with open(args.config, 'r') as ymlfile:
            metadata_config = yaml.load(ymlfile)
    except Exception as e:
        print("Missing configuration file")
        print(e)
        exit()
    return metadata_config


if args.config:
    # load metadata configuration
    metadata_config = load_metadata_config()
    print("Loading metadata configuration")


def list_to_string(lst):
    if lst is None:
        return '';
    else:
        return (';').join(lst)


def extract_values_from_resource(resource):
    row = []
    for field in metadata_config['CORE_FIELDS']:
        if field is 'tags':
            row.append(list_to_string(resource[field]))
        else:
            row.append(resource[field])
    for field in metadata_config['CUSTOM_FIELDS']:
        fields = field.split('__')
        # try to find value if it exists
        try:
            value = resource['customFields'][fields[0]][fields[1]]
        # otherwise pass null
        except:
            value = ''
        row.append(value)
    return row


def read_catalog_from_json(path_to_file):
    rows_to_write = []
    full_metadata = {'resources': []}
    with open(path_to_file, 'r') as json_file:
        catalog = json.load(json_file)
        for resource in catalog['resources']:
            rows_to_write.append(extract_values_from_resource(resource))
    return rows_to_write


def write_rows_to_csv(path_to_file, headers, rows):
    with open(path_to_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers)
        for row in rows:
            csvwriter.writerow(row)


csv_headers = metadata_config['CORE_FIELDS'] + metadata_config['CUSTOM_FIELDS']

rows_to_write = read_catalog_from_json(args.file)
write_rows_to_csv(args.output, csv_headers, rows_to_write)
print("Converted", args.file, "to CSV,", args.output)
