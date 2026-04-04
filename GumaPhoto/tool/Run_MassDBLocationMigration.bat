@echo off
echo [GumaPhoto DB Location Upgrade]
echo This will mass-migrate all locations in the database to the new Country-State-City-Borough-Village hierarchy using MetadataParser.
docker exec -it gumaphoto_app python tool/Run_MassDBLocationMigration.py
pause
