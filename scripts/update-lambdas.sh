echo Updating WalterAPI Auth source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-Auth-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI CreateUser source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-CreateUser-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI GetUser source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetUser-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI GetStock source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetStock-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI GetStatistics source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetStatistics-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI AddStock source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-AddStock-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI DeleteStock source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-DeleteStock-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI GetPrices source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetPrices-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI GetNewsSummary source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetNewsSummary-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI GetPortfolio source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetPortfolio-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI SendNewsletter source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-SendNewsletter-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI GetNewsletter source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetNewsletter-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI GetNewsletters source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetNewsletters-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI SendVerifyEmail source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-SendVerifyEmail-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI VerifyEmail source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-VerifyEmail-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI SendChangePasswordEmail source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-SendChangePasswordEmail-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI ChangePassword source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-ChangePassword-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI Subscribe source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-Subscribe-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI Unsubscribe source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-Unsubscribe-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI SearchStocks source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-SearchStocks-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI PurchaseNewsletterSubscription source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-PurchaseNewsletterSubscription-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI VerifyPurchaseNewsletterSubscription source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-VerifyPurchaseNewsletterSubscription-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterWorkflow AddNewsletterRequests source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterWorkflow-AddNewsletterRequests-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterWorkflow AddNewsSummaryRequests source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterWorkflow-AddNewsSummaryRequests-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterWorkflow CreateNewsletterAndSend source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterWorkflow-CreateNewsletterAndSend-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterWorkflow CreateNewsSummaryAndArchive source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterWorkflow-CreateNewsSummaryAndArchive-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI GetExpenses source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-GetExpenses-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI AddExpense source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-AddExpense-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterAPI DeleteExpense source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterAPI-DeleteExpense-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterCanary AuthUser source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-AuthUserCanary-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterCanary GetNewsletters source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-GetNewsletters-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterCanary GetNewsSummary source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-GetNewsSummaryCanary-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterCanary GetPortfolio source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-GetPortfolioCanary-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterCanary GetPrices source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-GetPricesCanary-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterCanary GetStock source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-GetStockCanary-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterCanary GetUser source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-GetUserCanary-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip \
&& echo Updating WalterCanary SearchStocks source code with artifact from S3 \
&& aws lambda update-function-code --function-name WalterCanary-SearchStocksCanary-dev --s3-bucket walter-backend-src --s3-key walter-backend.zip