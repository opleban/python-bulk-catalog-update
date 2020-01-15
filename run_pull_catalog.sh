 python get_catalog_json.py -d informatics.data.socrata.com -o ./json/old_catalog.json
 python convert_json_to_csv.py -f ./json/old_catalog.json -o ./catalog.csv -c ./domain_metadata.yml