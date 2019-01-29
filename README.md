# USS Survey 
An EDMC Plugin that logs USS and Hyperdiction details through a google form to a spreadsheet.

* Displays nearest patrol system prioritise by least visited.
* User can click on patrol location to view in EDSM
* User can click on clipboard icon to copy to clipboard

* When a user drops on a USS the USS details are [logged](https://docs.google.com/spreadsheets/d/1_LsPtmXS7aUGYTJ-OomdE4gsYqkrYsmS7qzSpIUhQ4s/edit?usp=sharing)
* The user can manually [log additional information](https://docs.google.com/spreadsheets/d/10SwarpGE6208lY0GpvSZogdk8s0m0bQXoZlZCWkDe1w/edit?usp=sharing) about the USS
* When a user is Hyperdicted the details are [logged](https://docs.google.com/spreadsheets/d/1grRDdXb6-6W1oxAVzPvvqTQDiVuExqAnvR97Q7cvrMA/edit?usp=sharing)
* The user can manually [log additional information](https://docs.google.com/spreadsheets/d/1IA3HxotFUXh9qJi3v-wtcenvMF-znamfQ8JtNJbiZdo/edit#gid=1466834969) about the Hyperdiction
* When a user arrives at a patrol destination their details are [logged.](https://docs.google.com/spreadsheets/d/1zlSh5fHg2ZM9fdLE4xl_GlPX0b0BFpbxarvKhRMUMi0/edit?usp=sharing)
* The patrol list is prioritised to the the nearest least visitied system is offered to the user.
* Users are notified of breaking news or upgrade availability

![Screenshot](screenshot.png)

Users may also report USS without dropping while they are in supercruise. 

![Screenshot](ussreport.png)


# Survey Results

![Statistics](https://docs.google.com/spreadsheets/d/e/2PACX-1vQGZ9meiqW_-5iDW2MKvwTBXK-RXJkCW53sNELRUH0jp99YZ1Qaj8yTYyFP89nwR803tHFRfEmENdjI/pubchart?oid=397514376&format=image)



[USS results spreadheet](https://docs.google.com/spreadsheets/d/10SwarpGE6208lY0GpvSZogdk8s0m0bQXoZlZCWkDe1w/edit?usp=sharing)
[Old USS results spreadheet](https://docs.google.com/spreadsheets/d/1_LsPtmXS7aUGYTJ-OomdE4gsYqkrYsmS7qzSpIUhQ4s/edit?usp=sharing)

[Hyperdiction results spreadheet](https://docs.google.com/spreadsheets/d/1grRDdXb6-6W1oxAVzPvvqTQDiVuExqAnvR97Q7cvrMA/edit?usp=sharing)

[Patrol Log spreadheet](https://docs.google.com/spreadsheets/d/1zlSh5fHg2ZM9fdLE4xl_GlPX0b0BFpbxarvKhRMUMi0/edit?usp=sharing)


You can also view the results on a the [Canonn 3D Map](https://map.canonn.technology/all/)

![Canonn Map](canonn3d.png)

# Installation
Download the [latest release](https://github.com/NoFoolLikeOne/EDMC-USS-Survey/releases), open the archive (zip) and extract the folder  to your EDMC plugin folder.

To install a downloaded plugin:

* On the Plugins settings tab press the “Open” button. This reveals the plugins folder where this app looks for plugins.
* Open the .zip archive that you downloaded and move the folder contained inside into the plugins folder.

You will need to re-start EDMC for it to notice the plugin.

# Troubleshooting

If you are using Kapersky Anti-Virus then it will probably be preventing the application from accessing the google spreadheets. Kaspersky Anti-Virus scans encrypted connections by substituting a requested security certificate with the self-signed one. Some applications like this plugin that initiate a connection reject the certificate, therefore failing to establish the connection. 

You will need to turn of  the encrypted connection scan

[Kapersy Support Issue](https://support.kaspersky.com/6851)


