echo Publishing new WalterAPI Auth Lambda version \
&& aws lambda publish-version --function-name WalterAPI-Auth-dev \
&& echo Publishing new WalterAPI CreateUser Lambda version \
&& aws lambda publish-version --function-name WalterAPI-CreateUser-dev \
&& echo Publishing new WalterAPI GetUser Lambda version \
&& aws lambda publish-version --function-name WalterAPI-GetUser-dev \
&& echo Publishing new WalterAPI GetStock Lambda version \
&& aws lambda publish-version --function-name WalterAPI-GetStock-dev \
&& echo Publishing new WalterAPI AddStock Lambda version \
&& aws lambda publish-version --function-name WalterAPI-AddStock-dev \
&& echo Publishing new WalterAPI DeleteStock Lambda version \
&& aws lambda publish-version --function-name WalterAPI-DeleteStock-dev \
&& echo Publishing new WalterAPI GetPrices Lambda version \
&& aws lambda publish-version --function-name WalterAPI-GetPrices-dev \
&& echo Publishing new WalterAPI GetNews Lambda version \
&& aws lambda publish-version --function-name WalterAPI-GetNews-dev \
&& echo Publishing new WalterAPI GetPortfolio Lambda version \
&& aws lambda publish-version --function-name WalterAPI-GetPortfolio-dev \
&& echo Publishing new WalterAPI SendNewsletter Lambda version \
&& aws lambda publish-version --function-name WalterAPI-SendNewsletter-dev \
&& echo Publishing new WalterAPI SendVerifyEmail Lambda version \
&& aws lambda publish-version --function-name WalterAPI-SendVerifyEmail-dev \
&& echo Publishing new WalterAPI VerifyEmail Lambda version \
&& aws lambda publish-version --function-name WalterAPI-VerifyEmail-dev \
&& echo Publishing new WalterAPI SendChangePasswordEmail Lambda version \
&& aws lambda publish-version --function-name WalterAPI-SendChangePasswordEmail-dev \
&& echo Publishing new WalterAPI ChangePassword Lambda version \
&& aws lambda publish-version --function-name WalterAPI-ChangePassword-dev \
&& echo Publishing new WalterAPI Subscribe Lambda version \
&& aws lambda publish-version --function-name WalterAPI-Subscribe-dev \
&& echo Publishing new WalterAPI Unsubscribe Lambda version \
&& aws lambda publish-version --function-name WalterAPI-Unsubscribe-dev \
&& echo Publishing new WalterNewsletters Lambda version \
&& aws lambda publish-version --function-name WalterNewsletters-dev \
&& echo Publishing new WalterBackend Lambda version \
&& aws lambda publish-version --function-name WalterBackend-dev