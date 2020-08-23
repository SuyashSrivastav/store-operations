# Store-Operations
Python based APIs to list products of a store and bill them.



How to use:

1.Make sure MongoDB is running on local and port 8080 is free.

2.Start by making sure Flask,Flask-JWT,wheel,PyMongo are installed on the system.If these are not installed use command "pip install flask" for flask and similarly for others.

3.Download the file "api.py" in Store folder on the system and start with running the "python api.py" command in the folder the file is downloaded to start the server.

4.Download the file "Store.postman_collection.json" from POSTMAN COLLECTION folder and import it in the postman application.

7.In the postman application go to Collections ----> Store .

8.Hit the API's present in the folders : User , Product ,Cart beginning with creation of User,place the request body with this required info in API's. For instance place token generated in the register/login API in headers as "access-token".

9.Register as an ADMIN and add products in the database.

10.Add the desired products to Cart and bill can be calculated by calling the get-bill API in Cart folder of collection..
