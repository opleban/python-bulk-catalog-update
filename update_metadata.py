import requests
import argparse
import os
from pprint import pprint
import json
import csv
import yaml

parser = argparse.ArgumentParser()

parser.add_argument("-f", "--file", help="required: provide path to CSV file containing updated metadata")
parser.add_argument("-d", "--domain", help="required: provide domain to update")
parser.add_argument("-c", "--config", help="required: provide path to metadata configuration yaml file")
parser.add_argument("-e", "--execute", help="Execute changes", action="store_true")
parser.add_argument("-o", "--output", help="optional: set output file to log results of the update.")
parser.add_argument("-v", "--verbose", help="Output verbose logs", action="store_true")

args = parser.parse_args()

try:
    # os.environ['SOCRATA_API_TOKEN']
    socrata_api_key_id = os.environ['SOCRATA_API_KEY_ID']
    socrata_api_key = os.environ['SOCRATA_API_KEY']
except:
    print('Please set your Socrata API Key ID and Socrata API Key.')
    exit()

execute_changes = False


def load_metadata_config():
    _config = {}
    try:
        with open(args.config, 'r') as ymlfile:
            _config = yaml.load(ymlfile)
    except Exception as e:
        print("Missing configuration file")
        print(e)
        exit()
    return _config


if args.verbose:
    print("Running verbosely")
if args.config:
    # load metadata configuration
    metadata_config = load_metadata_config()
    print("Loading metadata configuration")

if args.execute:
    print("Executing changes")
    execute_changes = True


def metadata_api_url(uuid):
    if execute_changes:
        return "https://" + args.domain + "/api/views/metadata/v1/" + uuid + "?strict=true"
    else:
        return "https://" + args.domain + "/api/views/metadata/v1/" + uuid + "?validateOnly=true&strict=true"


def get_metadata(uuid):
    print('')
    print('Getting metadata for: ' + uuid)
    return requests.get(metadata_api_url(uuid),
                        auth=(socrata_api_key_id, socrata_api_key)).json()


def patch_metadata(uuid, metadata):
    print('Updating metadata for: ' + uuid)
    headers = {'Content-Type': 'application/json'}
    res = requests.patch(metadata_api_url(uuid),
                         auth=(socrata_api_key_id, socrata_api_key),
                         headers=headers,
                         data=json.dumps(metadata))
    print('Metadata updated:', uuid)
    print('-------------------------')
    if args.verbose:
        pprint(res.json())


def read_csv_catalog(path_to_file):
    csv_metadata = []
    with open(path_to_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            reshaped_metadata = reshape_csv_row(row)
            csv_metadata.append(reshaped_metadata)
    return csv_metadata


# turn this into the shape the Metadata API expect
def reshape_csv_row(row):
    reshaped_metadata = {'customFields': {'Data Governance': {}}}
    for field in metadata_config['CORE_FIELDS']:
        try:
            reshaped_metadata[field] = row[field]
        except:
            print('missing field: ', field, ' in row: ', row)
    for field in metadata_config['CUSTOM_FIELDS']:
        split_fields = field.split("__")
        try:
            reshaped_metadata['customFields'][split_fields[0]][split_fields[1]] = row[field]
        except Exception as e:
            print("Field not present in row:", split_fields[0], split_fields[1])
            print(e)
    return reshaped_metadata


def find_current_version(uuid, catalog):
    for resource in catalog['resources']:
        if uuid == resource['id']:
            return resource
    print("Unable to find" + uuid + "in catalog. Ignoring for now.")
    return None


def is_valid_view(metadata):
    try:
        metadata['id']
        return True
    except:
        return False


def is_field_invalid(_dict, _field, valid_opts):
    return (_field in _dict) and (_dict[_field] not in valid_opts)


def field_exists_and_is_valid(_dict, _field, valid_opts):
    return (_field in _dict) and (_dict[_field] in valid_opts)


def diff_changes(change, current_version, _metadata_config):
    # ugh this is ugly
    diff = {}
    # for standard fields
    for _field in _metadata_config['CORE_FIELDS']:
        # check that field exists in both
        if (_field in change) and (_field in current_version):
            # check that there is a difference
            if change[_field] != current_version[_field]:
                # check that the difference isn't a case of '' and None
                if change[_field] != '':
                    diff[_field] = change[_field]
        # We can't patch a dataset with an invalid category, so let's just clear out invalid categories
        if _field == 'category':
            # check whether the diff has a valid category
            if is_field_invalid(diff, _field, _metadata_config['DOMAIN_CATEGORIES']):
                # check whether the current version has something valid
                if is_field_invalid(current_version, _field, _metadata_config['DOMAIN_CATEGORIES']):
                    print('Invalid CATEGORY in both diff and current version')
                    # if all else fails just pass in None if something else is present
                    diff[_field] = None
                    # and let's log to console what we're doing
                    print(current_version['id'], 'is either missing or had an invalid category. Replacing it '
                                                 'with null')
                else:
                    print(diff[_field], "is an invalid category value, not updating category. Check domain metadata "
                                        "configurations for valid configurations")
                    del diff[_field]

    if 'customFields' in change:
        for field in _metadata_config['CUSTOM_FIELDS']:
            custom_field = field.split("__")[1]
            # if custom fields is present in the current version, let's modify it
            if (current_version['customFields'] is not None) and ('Data Governance' in current_version['customFields']):
                # go through one by one
                if custom_field in current_version['customFields']['Data Governance']:
                    # if values are different
                    if change['customFields']['Data Governance'][custom_field] != \
                            current_version['customFields']['Data Governance'][custom_field]:
                        # add custom fields to diff if not already there
                        if 'customFields' not in diff:
                            diff['customFields'] = {}
                            diff['customFields']['Data Governance'] = {}
                        # if change is actually an erase
                        if change['customFields']['Data Governance'][custom_field] == '':
                            diff['customFields']['Data Governance'][custom_field] = None
                        # else make change
                        else:
                            diff['customFields']['Data Governance'][custom_field] = \
                                change['customFields']['Data Governance'][custom_field]
            else:
                # check for non-empty changes and include those
                if change['customFields']['Data Governance'][custom_field] != '':
                    if 'customFields' not in diff:
                        diff['customFields'] = {}
                        diff['customFields']['Data Governance'] = {}
                    diff['customFields']['Data Governance'][custom_field] = change['customFields']['Data Governance'][
                        custom_field]
    return diff


def update_metadata(updated_changes):
    for change in updated_changes:
        uuid = change['id']
        current_version = get_metadata(uuid)
        if is_valid_view(current_version):
            diff = diff_changes(change, current_version, metadata_config)
            pprint(diff)
            if not diff:
                print("No changes for: ", uuid)
                print('-------------------------')
            else:
                if args.verbose:
                    print("startdiff---------------------------startdiff")
                    pprint(diff)
                    print("enddiff---------------------------enddiff")
                patch_metadata(uuid, diff)

        else:
            print("View" + uuid + "not found. Ignoring for now.")


print('Getting changes from CSV:', args.file)
updated_changes = read_csv_catalog(args.file)
print('Begin updating catalog at:', args.domain)
update_metadata(updated_changes)
# output_updated_catalog_to_csv(updated_catalog)
