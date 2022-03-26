Belgian pharmacies
================================

This small github repo dumps each day the list of pharmacies in Belgium published by [AFMPS](https://www.afmps.be/fr) and [OpenStreetMap](https://www.openstreetmap.org/), and maintains history in JSON files :
* [stats.json](stats.json) : Statistics per date :
   - Pharmacies per zipCode (active, temporarily suspended, total)
   - Pharmacies per region (Brussels / Flanders / Wallonia)
* [data_afmps](data_afmps) : JSON exports of pharmacies per date
* [last-pharmacies_afmps.json](last-pharmacies_afmps.json): The most recent JSON export of pharmacies in AFMPS
* [last-pharmacies_osm.json](last-pharmacies_osm.json): The most recent JSON export of pharmacies in Open Street Map
* [last-pharmacies_enhancedVersion.json](last-pharmacies_enhancedVersion.json) : The most recent JSON export of pharmacies that combines data from AFMPS and Open Street Map

How do you do that?
-------------------

AFMPS publishes at irregular times a up to date list of pharmacies.
That is however a Excel file that is a bit hard to exploit :

 | Vergunningsnummer Numéro d'autorisation | Naam Nom | Adres Adresse     | Postcode Code Postal | Gemeente Commune  | Status Statut | Vergunninghouder Détenteur d'autorisation   | Uitbater Exploitant | X (Lambert 2008) | Y (Lambert 2008)
 | --------------------------------------- | ---------------- | ----------------- | -------------------- | ----------------- | ------------- | ------------------------------------------- | ------------------- | ---------------- | ----------------
 | 913007   | Familia  | Rue Du Chene 38 C | 5590                 | Ciney  | \*(1)  | L'ECONOMIE POPULAIRE (KBO-BCE : 0401388176) | Idem   | 699195.0625 | 606744.8125     
 | 923702 | Pharmacie Demars | Rue D'anthee 58   | 5644                 | Mettet | null | DEMARS (KBO-BCE : 0689526478) | Idem | 674963 | 609546.375      
 | 123502  | Keustermans | Kapelstraat 30    | 2223 | Heist-op-den-berg | null | Blockx (KBO-BCE : 0814823160) | Idem  | 673903.875 | 689536.9375
 | 111009 | Van Butsele | Thibautstraat 139 | 2140 | Antwerpen | null | Van Butsele (KBO-BCE : 0541895646) | BVBA Apotheker Karen Van Butsele (KBO-BCE : 0899874740) | 655857.25 | 710446.875 

After some Python magic, we can turn that into something useful, like with Jupyter notebook :

Why do you do that?
-------------------

Several reasons :
* Open data sources are not always up to date or present for each region in Belgium
    - [Pharmacies at Brussels](https://data.gov.be/en/node/120109)
* Websites like [this one](https://www.pharmacie.be/) don't have a good UX
* A good way to track changes (new entries, suspended entries, ...) for pharmacies
* Because I can ;)

License
-------------------

Belgian pharmacies © 2022 by Jacques Yakoub is licensed under CC BY-NC-SA 4.0. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/4.0/