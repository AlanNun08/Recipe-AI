#!/bin/bash

# Set environment variables for Cloud Run deployment
# Replace these values with your actual credentials before running

echo "Setting up Cloud Run environment variables..."

gcloud run services update buildyoursmartcart \
  --project=sunlit-vortex-466800-q8 \
  --region=us-central1 \
  --set-env-vars="NODE_ENV=production" \
  --set-env-vars="MONGO_URL=YOUR_MONGODB_ATLAS_CONNECTION_STRING" \
  --set-env-vars="DB_NAME=buildyoursmartcart_production" \
  --set-env-vars="OPENAI_API_KEY=YOUR_OPENAI_API_KEY" \
  --set-env-vars="STRIPE_SECRET_KEY=YOUR_STRIPE_SECRET_KEY" \
  --set-env-vars="STRIPE_PUBLISHER_API_KEY=YOUR_STRIPE_PUBLISHER_API_KEY" \
  --set-env-vars="WALMART_CONSUMER_ID=YOUR_WALMART_CONSUMER_ID" \
  --set-env-vars="WALMART_KEY_VERSION=1" \
  --set-env-vars="WALMART_PRIVATE_KEY=YOUR_WALMART_PRIVATE_KEY" \
  --set-env-vars="MAILJET_API_KEY=YOUR_MAILJET_API_KEY" \
  --set-env-vars="MAILJET_SECRET_KEY=YOUR_MAILJET_SECRET_KEY" \
  --set-env-vars="SENDER_EMAIL=noreply@buildyoursmartcart.com" \
  --set-env-vars="SECRET_KEY=YOUR_STRONG_SECRET_KEY_32_CHARS_MIN"

echo "Environment variables updated!"