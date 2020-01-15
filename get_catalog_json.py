import requests
import argparse
import os
from pprint import pprint
import json
import csv

# uuid = "i79a-kyxr"
# initiate the parser
parser = argparse.ArgumentParser()

parser.add_argument("-d", "--domain", help="required: set the target domain")
parser.add_argument("-o", "--output", help="required: set output file for json")
parser.add_argument("-v", "--verbose", help="Output verbose logs", action="store_true")

args = parser.parse_args()
# execute_changes = False

try:
    socrata_api_key_id = os.environ['SOCRATA_API_KEY_ID']
    socrata_api_key = os.environ['SOCRATA_API_KEY']
except:
    print('Please set your Socrata API Key ID and Socrata API Key.')
    exit()

if args.domain:
    print("Target domain is %s" % args.domain)
    domain = args.domain

def metadata_api_url(uuid):
    # if execute_changes:
    # 	return "https://" + args.domain + "/api/views/metadata/v1/" + uuid + "?strict=true"
    # else:
    return "https://" + args.domain + "/api/views/metadata/v1/" + uuid + "?validateOnly=true&strict=true"


def get_metadata(uuid):
    if args.verbose:
        print('Getting metadata for: ' + uuid)
    return requests.get(metadata_api_url(uuid),
                        auth=(socrata_api_key_id, socrata_api_key)).json()


def get_non_derived_catalog():
    catalog_api_url = "https://" + args.domain + '/api/catalog/v1?domains=' + args.domain + "&derived=false&limit=10000&published=true&only=datasets"
    print("Hitting " + catalog_api_url)
    return requests.get(catalog_api_url, auth=(socrata_api_key_id, socrata_api_key)).json()


def extract_dataset_f_x_f(catalog):
    _catalog_ids = {'ids': list(map(lambda ds: ds['resource']['id'], catalog['results']))}
    return _catalog_ids


def write_json_file(path_to_file, jsn):
    with open(path_to_file, 'w') as outfile:
        json.dump(jsn, outfile)


def write_to_csv(path_to_file, lst, header=["ids"]):
    with open(path_to_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(header)
        for item in lst:
            csvwriter.writerow([item])


def get_catalog_metadata(uuids):
    catalog = {'resources': []}
    for uuid in uuids:
        catalog['resources'].append(get_metadata(uuid))
    return catalog


# get catalog
catalog_json = get_non_derived_catalog()

# pullout ids
catalog_ids = extract_dataset_f_x_f(catalog_json)

# write results to csv
# write_to_csv('./catalog_ids.csv', catalog_ids['ids'], ['ids'])

catalog_metadata = get_catalog_metadata(catalog_ids['ids'])

write_json_file(args.output, catalog_metadata)
