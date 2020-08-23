from flask import Flask, jsonify, request, Response
import datetime
import jwt
from bson.objectid import ObjectId
import json
from functools import wraps
import pymongo
app = Flask(__name__)


app.config['SECRET_KEY'] = 'abcdefghijklmnop'
app.config['JWT_ALGORITHM'] = 'HS256'


try:
    mongo = pymongo.MongoClient(
        host="localhost",
        port=27017,
        serverSelectionTimeoutMS=3000
    )
    db = mongo.store
    mongo.server_info()
    print(">>>Database Connected!!")
except:
    print(">>>Error connecting to database!")


#######################################>>>>>>>>>>>>>>>>>.........AUTHORIZATION ROUTES...................<<<<<<<<<<<<<<<<<<<<<<#################################
"""
>>>Authorization through JWT Token
"""


def authenticate(func):
    @wraps(func)
    def authenticator(*args, **kwargs):
        try:
            token = None
            if request.headers['access-token']:
                token = request.headers['access-token'].encode(
                    'ascii', 'ignore')
                if not token:
                    return Response(status=404, response=json.dumps({"message": "Validation failed"}))
        except:
            return Response(status=404, response=json.dumps({"message": "Validation failed"}))

        try:
            data = jwt.decode(
                token, app.config['SECRET_KEY'], app.config['JWT_ALGORITHM'])['id']
            current_user = list(db.users.find(
                {'_id': ObjectId(data), 'is_active': True}))
            current_user[0]['_id'] = current_user[0]['_id']
            # print(data)
        except:
            return Response(status=404, response=json.dumps({"message": "Validation failed"}))

        return func(current_user, *args, **kwargs)
    return authenticator


#######################################>>>>>>>>>>>>>>>>>.........USER ROUTES...................<<<<<<<<<<<<<<<<<<<<<<#################################
"""
>>>Registeration can be done by passing "name","email" ,"password", "address" and "user_type .
>>>"user_type" can be "ADMIN" or "USER"
>>>"token" found in reponse of this API will be placed in header as "access-token" to perform authorization.
"""


@app.route('/register-user', methods=['POST'])
def add_user():
    try:
        name = request.json['name']
        address = request.json['address']
        email = request.json['email']
        password = request.json['password']
        user_type = request.json['user_type']

        if not email:
            return Response(status=404, response=json.dumps({"message": "Missing email parameter"}))
        if not password:
            return Response(status=404, response=json.dumps({"message": "Missing password parameter"}))
        if not user_type:
            user_type = "USER"

        data = list(db.users.find({'email': email, 'is_active': True}))
        if (len(data) > 0):

            data[0]['_id'] = str(data[0]['_id'])
            token = jwt.encode({'id': data[0]['_id'], 'exp': datetime.datetime.utcnow()+datetime.timedelta(minutes=300)},
                               app.config['SECRET_KEY'], app.config['JWT_ALGORITHM']).decode('utf-8')

            return Response(
                response=json.dumps(
                    {"message": "user exists", "token": token}),
                status=200,
                mimetype="application/json")
        else:
            try:
                is_admin = False
                if (user_type == 'ADMIN'):
                    is_admin = True

                dbResponse = db.users.insert_one({
                    'name': name,
                    'address': address,
                    'email': email,
                    'password': password,
                    'is_active': True,
                    'is_admin': is_admin
                })
                if dbResponse:
                    token = jwt.encode({'id': str(dbResponse.inserted_id), 'exp': datetime.datetime.utcnow()+datetime.timedelta(minutes=300)},
                                       app.config['SECRET_KEY'], app.config['JWT_ALGORITHM']).decode('utf-8')
                    # print(token)

                    return Response(
                        response=json.dumps(
                            {"message": "user created", "token": token}),
                        status=200,
                        mimetype="application/json")
                else:
                    return Response(status=404, response=json.dumps({"message": "Creation failed"}))
            except:
                return Response(status=404, response=json.dumps({"message": "Creation failed"}))
    except:
        return Response(status=404, response=json.dumps({"message": "Creation failed"}))


########################################################################################################################################################
"""
>>>Login can be done by passing "email" and "password" of a registered User in the request.
"""


@app.route('/login', methods=['GET'])
def login():
    try:
        email = request.json['email']
        password = request.json['password']
        data = list(db.users.find(
            {'email': email, 'password': password, 'is_active': True}))

        if (len(data) > 0):
            data[0]['_id'] = str(data[0]['_id'])
            token = jwt.encode({'id': data[0]['_id'], 'exp': datetime.datetime.utcnow()+datetime.timedelta(minutes=300)},
                               app.config['SECRET_KEY'], app.config['JWT_ALGORITHM']).decode('utf-8')

            return Response(
                response=json.dumps(
                    {"message": "login success", "token": token}),
                status=200,
                mimetype="application/json")
        else:
            return Response(response=json.dumps({"message": "user not found"}), status=500, mimetype="application/json")

    except Exception as ex:
        return Response(response=json.dumps({"message": "user not found", 'error': ex}), status=500, mimetype="application/json")


##################################################################################################################################################
"""
>>>Details of a User can be seen by passing "access-token" in header.
"""


@app.route('/user-detail', methods=['GET'])
@authenticate
def get_user_details(current_user):
    try:
        data = list(db.users.find(
            {'_id': ObjectId(current_user[0]['_id']), 'is_active': True}))

        if (len(data) > 0):
            data[0]['_id'] = str(data[0]['_id'])
            del data[0]['password']
            return Response(
                response=json.dumps({"user_detail": data[0]}),
                status=200,
                mimetype="application/json")
        else:
            return Response(response=json.dumps({"message": "user not found"}), status=500, mimetype="application/json")

    except Exception as ex:
        return Response(response=json.dumps({"message": "user not found", 'error': ex}), status=500, mimetype="application/json")


######################################>>>>>>>>>>>>>>>>>........PRODUCT ROUTES...................<<<<<<<<<<<<<<<<<<<<<<##########################################################################################################
"""
>>>ADMIN Users can add the Product by passing "product_name" , "price" and "description" in the request.
>>>"token" will be passed in Headers with key as "access-token"
"""


@app.route('/add-product', methods=['POST'])
@authenticate
def add_product(current_user):
    try:
        if current_user[0]['is_admin']:
            product_name = request.json['product_name']
            price = request.json['price']
            description = request.json['description']

            data = list(db.products.find({'product_name': product_name}))

            if (len(data) > 0):
                data[0]['_id'] = str(data[0]['_id'])
                return Response(
                    response=json.dumps(
                        {"message": "product exists", "product_id": data[0]['_id']}),
                    status=200,
                    mimetype="application/json")
            else:
                try:
                    data = list(db.products.find({}))
                    dbResponse = db.products.insert_one({
                        '_id': len(data)+1,
                        'product_name': product_name,
                        'price': price,
                        'description': description,
                        'is_available': True})
                    return Response(
                        response=json.dumps(
                            {"message": "product created", "product_id": f"{dbResponse.inserted_id}"}),
                        status=200,
                        mimetype="application/json")
                except Exception as ex:
                    return Response(status=404, response=json.dumps({"error": ex}))
        else:
            return Response(status=404, response=json.dumps({"message": "ADMIN NOT FOUND"}))
    except:
        return Response(status=404, response=json.dumps({"message": "Creation Failed"}))


######################################################################################################################################################
"""
>>>All registered Users can see the list of products available.
>>>"token" will be passed in Headers with key as "access-token"
"""


@app.route('/product-list', methods=['GET'])
@authenticate
def get_product_list(user):
    try:
        data = list(db.products.find({'is_available': True}))
        # print(data)
        if (len(data) > 0):
            return Response(
                response=json.dumps({'products': data}),
                status=200,
                mimetype="application/json")
        else:
            return Response(response=json.dumps({"message": "products not found"}), status=500, mimetype="application/json")

    except Exception as ex:
        return Response(response=json.dumps({"message": "user not found", 'error': ex}), status=500, mimetype="application/json")


#####################################################################################################################################################
"""
>>>All registered Users can see the product list.
>>>"token" will be passed in Headers with key as "access-token"
"""


@app.route('/mark-unavailable', methods=['POST'])
@authenticate
def mark_product_unavailable(user):
    try:
        if user[0]['is_admin']:
            product_id = (request.json['product_id'])

            list(db.products.update({'_id': int(product_id)}, {
                 '$set': {'is_available': False}}))

            return Response(
                response=json.dumps({"message": "product status changed"}),
                status=200,
                mimetype="application/json")
        else:
            return Response(response=json.dumps({"message": "ADMIN NOT FOUND"}), status=500, mimetype="application/json")

    except Exception as ex:
        return Response(response=json.dumps({"message": "update failed", "err": ex}), status=500, mimetype="application/json")


#########################################################################################################################################################
"""
>>>ADMIN Users can delete the Product permanantly from database by passing "product_id" in the request.
>>>"token" will be passed in Headers with key as "access-token"
"""


@app.route('/delete-product', methods=['POST'])
@authenticate
def delete_product(user):
    try:
        if user[0]['is_admin']:
            product_id = (request.json['product_id'])

            delete_product = list(db.products.remove({'_id': int(product_id)}))

            if (delete_product):
                return Response(
                    response=json.dumps({"message": "deleted"}),
                    status=200,
                    mimetype="application/json")
            else:
                return Response(response=json.dumps({"message": "delete failed"}), status=500, mimetype="application/json")
        else:
            return Response(response=json.dumps({"message": "ADMIN NOT FOUND"}), status=500, mimetype="application/json")

    except:
        return Response(response=json.dumps({"message": "delete failed"}), status=500, mimetype="application/json")


########################################>>>>>>>>>>>>>>>>>.........ORDER ROUTES...................<<<<<<<<<<<<<<<<<<<<<<###########################################################################################################
"""
>>>All registered Users can add Products to Cart by passing "product_id" and "quantity" in the request.
>>>"token" will be passed in Headers with key as "access-token"
"""


@app.route('/add-to-cart', methods=['POST'])
@authenticate
def add_to_cart(user):
    try:
        product_id = request.json['product_id']
        quantity = request.json['quantity']

        product_data = list(db.products.find({'_id': int(product_id)}))
        if (len(product_data) > 0):
            data = list(db.orders.find(
                {'user_id': ObjectId(user[0]['_id']), 'status': 'PENDING'}))
            if (len(data) > 0):
                # print(data)
                try:
                    db.orders.update_one({'_id': data[0]['_id']}, {'$addToSet': {'cart_items': {
                        'product_id': product_data[0]['_id'],
                        'quantity': quantity,
                        'name': product_data[0]['product_name'],
                        'price': product_data[0]['price'],
                        'description': product_data[0]['description']
                    }}})
                    # print(order_update)

                    order_data = list(db.orders.find(
                        {'user_id': ObjectId(user[0]['_id']), 'status': 'PENDING'}))
                    # order_data[0]['_id']=str(data[0]['_id'])

                    return Response(
                        response=json.dumps(
                            {"message": "added to cart", "cart_items": order_data[0]['cart_items']}),
                        status=200,
                        mimetype="application/json")

                except:
                    return Response(response=json.dumps({"message": "add failed"}), status=500, mimetype="application/json")
            else:
                try:
                    dbResponse = db.orders.insert_one({
                        'user_id': ObjectId(user[0]['_id']),
                        'cart_items': [{
                            'product_id': product_data[0]['_id'],
                            'quantity': quantity,
                            'name': product_data[0]['product_name'],
                            'price': product_data[0]['price'],
                            'description':product_data[0]['description']
                        }],
                        'amount': 0,
                        'status': 'PENDING'})

                    order_data = list(db.orders.find(
                        {'_id': dbResponse.inserted_id}))

                    return Response(
                        response=json.dumps(
                            {"message": "added to cart", "cart_items": order_data[0]['cart_items']}),
                        status=200,
                        mimetype="application/json")

                except:
                    return Response(response=json.dumps({"message": "add failed"}), status=500, mimetype="application/json")
        else:
            return Response(response=json.dumps({"message": "product not found"}), status=500, mimetype="application/json")
    except:
        return Response(response=json.dumps({"message": "add failed"}), status=500, mimetype="application/json")


#######################################################################################################################################################
"""
>>>All registered Users can remove Products added to Cart by passing "product_id" in the request.
>>>"token" will be passed in Headers with key as "access-token"
"""


@app.route('/remove-from-cart', methods=['POST'])
@authenticate
def remove_from_cart(user):
    try:
        product_id = request.json['product_id']
        list(db.orders.update({'user_id': ObjectId(user[0]['_id'])}, {
             '$pull': {'cart_items': {'product_id': int(product_id)}}}))

        order_data = list(db.orders.find(
            {'user_id': ObjectId(user[0]['_id']), 'status': 'PENDING'}))

        if (len(order_data) > 0):
            return Response(
                response=json.dumps(
                    {"message": "removed from cart", "cart_items": order_data[0]['cart_items']}),
                status=200,
                mimetype="application/json")
        else:
            return Response(response=json.dumps({"message": "remove failed"}), status=500, mimetype="application/json")
    except:
        return Response(response=json.dumps({"message": "remove failed"}), status=500, mimetype="application/json")


#####################################################################################################################################################
"""
>>>All registered Users can change quantity of Products added to Cart by passing "product_id" and "new_quantity" in the request.
>>>"token" will be passed in Headers with key as "access-token"
"""


@app.route('/change-quantity', methods=['POST'])
@authenticate
def change_quantity(user):
    try:
        product_id = (request.json['product_id'])
        new_quantity = request.json['new_quantity']

        list(db.orders.update({'user_id': ObjectId(user[0]['_id']), 'cart_items.product_id': int(
            product_id)}, {'$set': {'cart_items.$.quantity': int(new_quantity)}}))

        order_data = list(db.orders.find(
            {'user_id': ObjectId(user[0]['_id']), 'status': 'PENDING'}))

        if (len(order_data) > 0):
            return Response(
                response=json.dumps(
                    {"message": "quantity changed", "cart_items": order_data[0]['cart_items']}),
                status=200,
                mimetype="application/json")
        else:
            return Response(response=json.dumps({"message": "change failed"}), status=500, mimetype="application/json")

    except:
        return Response(response=json.dumps({"message": "change failed"}), status=500, mimetype="application/json")


######################################################################################################################################################
"""
>>>All registered Users can checkout the Products added to Cart and the total billing amount.
>>>"token" will be passed in Headers with key as "access-token"
"""

@app.route('/get-bill', methods=['GET'])
@authenticate
def get_bill(user):
    try:
        order_data = list(db.orders.aggregate([
            {'$match': {'$expr': {'$and': [
                {'$eq': ['$status', 'PENDING']}, {'$eq': ['$user_id', ObjectId(user[0]['_id'])]}]}}},
            {'$unwind': '$cart_items'},
            {
                '$group': {
                    '_id': '$user_id',
                    'cart_items': {'$push': '$cart_items'},
                    'amount': {'$sum': {'$multiply': ['$cart_items.price', '$cart_items.quantity']}},
                    'status':{'$first': '$status'}
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'user_id': '$_id',
                    'name': {'$ifNull': [user[0]['name'], ""]},
                    'address': {'$ifNull': [user[0]['address'], ""]},
                    'email': {'$ifNull': [user[0]['email'], ""]},
                    'amount': 1,
                    'products': '$cart_items'
                }
            }
        ]))
        # print(order_data)

        if (len(order_data) > 0):
            order_data[0]['user_id'] = str(order_data[0]['user_id'])
            return Response(
                response=json.dumps(
                    {"message": "user bill details", "bill": order_data[0]}),
                status=200,
                mimetype="application/json")
        else:
            return Response(response=json.dumps({"message": "bill not found"}), status=500, mimetype="application/json")

    except:
        return Response(response=json.dumps({"message": "bill generation failed"}), status=500, mimetype="application/json")

#####################################################################################################################################################


if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)
