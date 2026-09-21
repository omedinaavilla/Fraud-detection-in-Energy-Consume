About
The data provided by STEG is composed of two files. The first one is comprised of client data and the second one contains billing history from 2005 to 2019.

There are 2 .zip files for download, train.zip, and test.zip and a SampleSubmission.csv. In each .zip file you will find a client and invoice file.

Variable definitions

Client:

Client_id: Unique id for client
District: District where the client is
Client_catg: Category client belongs to
Region: Area where the client is
Creation_date: Date client joined
Target: fraud:1 , not fraud: 0
Invoice data

Client_id: Unique id for the client
Invoice_date: Date of the invoice
Tarif_type: Type of tax
Counter_number:
Counter_statue: takes up to 5 values such as working fine, not working, on hold statue, ect
Counter_code:
Reading_remarque: notes that the STEG agent takes during his visit to the client (e.g: If the counter shows something wrong, the agent gives a bad score)
Counter_coefficient: An additional coefficient to be added when standard consumption is exceeded
Consommation_level_1: Consumption_level_1
Consommation_level_2: Consumption_level_2
Consommation_level_3: Consumption_level_3
Consommation_level_4: Consumption_level_4
Old_index: Old index
New_index: New index
Months_number: Month number
Counter_type: Type of counter