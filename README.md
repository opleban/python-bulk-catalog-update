# Catalog Bulk Metadata Update

This is a slight overhaul of our catalog bulk metadata updater, using Python instead of NodeJS.

## Instructions

### Set Up
#### Installation
Run `pip install -r ./requirements.txt` to load the necessary the dependencies.

#### Configuring domain_metadata.yml
I'm using a simple yml file, `domain_metadata.yml` to configure the script for a domain's metadata configuration rather than querying the platform for simplicity's sake. Update the domain_metadata.yml as necessary with any necessary custom fields under "CUSTOM_FIELDS". Please note, for now this assumes that all Custom Fields are nested under at least one field set (i.e. "Data Governance" is a field set with multiple fields within it such as "System of Record"). No changes are necessary to "CORE_FIELDS" unless any large platform changes to dataset metadata are done. In the future support for tags can be added to this script.

Also make sure to update the "DOMAIN_CATEGORIES" with the domain-specific categories if that changes. Those categories can be managed at `/admin/metadata`.

#### Configure run bash scripts
I've included a couple bash scripts to simplify using the scripts.

* `run_pull_catalog.sh`
As the name suggests this one will pull down the current version of your catalog and output it into a csv file. By default this pulls from `informatics.data.socrata.com` and outputs the catalog to `catalog.csv`.

* `run_update_catalog.sh`
This one will read update the catalog based on any changes you've made to catalog.csv. By default this also points to `informatics.data.socrata.com`. 

## Notes 
Please note that for the platform field "category", you won't be able to save a dataset with an invalid category value. This includes existing datasets that may have now invalid category values (say if the metadata configuration for the domain changed since the dataset's metadata was inititally updated). For those datasets with invalid category values, even if no values are passed into through the modified catalog file, the script will replace the existing value with `null`. 

In general though, the script will only update the datasets that are included in the CSV and where metadata values have changed. It should not update datasets that are included in the CSV if their values remain unchanged, except in the above case where the category value is invalid.