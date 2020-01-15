# Updated the metadata
python update_metadata.py -f catalog.csv -d informatics.data.socrata.com -c domain_metadata.yml -e

# Now let's pull down our updated catalog
python get_catalog_json.py -d informatics.data.socrata.com -o ./json/new_catalog.json
python convert_json_to_csv.py -f ./json/new_catalog.json -o ./new_catalog.csv -c domain_metadata.yml