#!/bin/bash

# Define the image URI as a variable
IMAGE_URI="010526272437.dkr.ecr.us-east-1.amazonaws.com/walter/api:latest"

echo Updating WalterAPI Auth source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-Auth-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterAPI CreateUser source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-CreateUser-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterAPI GetUser source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetUser-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterAPI GetStock source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetStock-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterAPI GetStatistics source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetStatistics-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterAPI AddStock source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-AddStock-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterAPI DeleteStock source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-DeleteStock-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterAPI GetPrices source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetPrices-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterAPI GetNewsSummary source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetNewsSummary-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterAPI GetPortfolio source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetPortfolio-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterAPI SendNewsletter source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-SendNewsletter-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterAPI GetNewsletter source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetNewsletter-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterAPI GetNewsletters source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetNewsletters-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterAPI SendVerifyEmail source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-SendVerifyEmail-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterAPI VerifyEmail source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-VerifyEmail-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterAPI SendChangePasswordEmail source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-SendChangePasswordEmail-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterAPI ChangePassword source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-ChangePassword-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterAPI Subscribe source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-Subscribe-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterAPI Unsubscribe source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-Unsubscribe-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterAPI SearchStocks source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-SearchStocks-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterAPI PurchaseNewsletterSubscription source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-PurchaseNewsletterSubscription-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterAPI VerifyPurchaseNewsletterSubscription source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-VerifyPurchaseNewsletterSubscription-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterWorkflow AddNewsletterRequests source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterWorkflow-AddNewsletterRequests-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterWorkflow AddNewsSummaryRequests source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterWorkflow-AddNewsSummaryRequests-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterWorkflow CreateNewsletterAndSend source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterWorkflow-CreateNewsletterAndSend-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip --no-cli-pager \
&& echo Updating WalterWorkflow CreateNewsSummaryAndArchive source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterWorkflow-CreateNewsSummaryAndArchive-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterAPI GetExpenses source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetExpenses-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterAPI AddExpense source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-AddExpense-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterAPI DeleteExpense source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-DeleteExpense-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterCanary AuthUser source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-AuthUserCanary-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterCanary GetNewsletters source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-GetNewsletters-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterCanary GetNewsSummary source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-GetNewsSummaryCanary-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterCanary GetPortfolio source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-GetPortfolioCanary-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterCanary GetPrices source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-GetPricesCanary-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterCanary GetStock source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-GetStockCanary-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterCanary GetUser source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-GetUserCanary-dev --image-uri $IMAGE_URI --no-cli-pager \
&& echo Updating WalterCanary SearchStocks source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-SearchStocksCanary-dev --image-uri $IMAGE_URI --no-cli-pager