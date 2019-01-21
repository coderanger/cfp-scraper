upload:
	aws s3 sync site s3://cfpcalendar.com/ --acl public-read
