# python-heatwave-api

Return number of heatwave days for the longest heatwave historically and projected for a given latitude and longitude.

# Deployment

To deploy on Google Cloud Functions install gcloud and run the following:

`gcloud functions deploy heatwave_api --runtime python37 --trigger-http`