
from flask import Blueprint, render_template, request, redirect, url_for, flash ,session
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def home():
    print("SESSION:", dict(session))

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    query = "SELECT id, name, description FROM restaurants WHERE is_active = TRUE"
    cursor.execute(query)
    restaurants = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("home.html", restaurants=restaurants)


###########################################################################################################

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "customer")

        if not name or not email or not password:
            return render_template("register.html", error= "name or email can't empty")

        if role not in ("customer", "restaurant", "driver"):
            return render_template("register.html", error= "role is invalid")

        hashed_password = generate_password_hash(password)

        db = get_db_connection()
        cursor = db.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                (name, email, hashed_password, role)
            )
            db.commit()
        except Exception:
            db.rollback()
            return render_template("register.html", error= "email may already exsist")
        finally:
            cursor.close()
            db.close()

        return redirect(url_for("auth.login"))

    return render_template("register.html")


#############################################################################################################





@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT * FROM users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()
        finally:
            cursor.close()
            db.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            if user["role"] == "restaurant":
                return redirect(url_for("restaurant.restaurant_dashboard"))

            else:
                return redirect(url_for("auth.home"))

        return render_template( "login.html" , error = "Invalid email or password")

    return render_template("login.html")


#################################################################################################################


@auth_bp.route("/restaurant/<int:restaurant_id>")
def restaurant_menu(restaurant_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT id, name, description FROM restaurants "
            "WHERE id = %s AND is_active = TRUE",
            (restaurant_id,)
        )
        restaurant = cursor.fetchone()

        if restaurant is None:
            return "Restaurant not found", 404

        cursor.execute(
            "SELECT id, name, description, price FROM menu_items "
            "WHERE restaurant_id = %s AND is_available = TRUE",
            (restaurant_id,)
        )
        menu_items = cursor.fetchall()
    finally:
        cursor.close()
        db.close()

    return render_template(
        "menu.html",
        restaurant=restaurant,
        menu_items=menu_items
    )



#####################################################################################################################


@auth_bp.route("/add-to-cart/<int:item_id>",methods = ["POST"])
def add_to_cart(item_id):
    if "user_id" not in session : 
        return redirect(url_for("auth.login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("select id from menu_items where id=%s and is_available = True",(item_id,))
    item = cursor.fetchone()

    if item is None:
        cursor.close()
        db.close()
        return "food is not available" , 404

    cursor.execute("select id from cart_items where user_id = %s and menu_item_id = %s ",(session["user_id"],item_id))

    exsisting_item = cursor.fetchone()

    if exsisting_item:
        cursor.execute("update cart_items set quantity = quantity+1 where user_id = %s and menu_item_id = %s" , (session["user_id"] , item_id))
    else:
        cursor.execute("insert into cart_items(user_id , menu_item_id , quantity) values (%s , %s , %s)",(session["user_id"] , item_id , 1))
    
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("auth.cart"))





##############################################################################################################################

@auth_bp.route("/cart")
def cart():
    if "user_id" not in session : 
        return redirect(url_for("auth.login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""select ci.id , ci.quantity , mi.name , mi.price , (ci.quantity*mi.price) as subtotal
     from cart_items ci join menu_items mi on ci.menu_item_id = mi.id where ci.user_id = %s""",(session["user_id"],))

    items = cursor.fetchall()
    cursor.close()
    db.close()

    total = sum(item["subtotal"] for item in items)

    return render_template("cart.html",items=items , total = total)



##############################################################################################################################

@auth_bp.route("/remove-from-cart/<int:cart_item_id>" , methods = ["POST"])
def remove_from_cart(cart_item_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM cart_items WHERE id = %s AND user_id = %s",
        (cart_item_id, session["user_id"])
    )
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for("auth.cart"))



###############################################################################################################################

@auth_bp.route("/increase-cart-item/<int:cart_item_id>" , methods=["POST"])
def increase_cart_quantity(cart_item_id):
    if "user_id" not in session:
         return redirect(url_for("auth.login"))
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""update cart_items set quantity = quantity + 1 where user_id = %s and id = %s """ ,(session["user_id"],cart_item_id))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("auth.cart"))


###############################################################################################################################

@auth_bp.route("/decrease-cart-item/<int:cart_item_id>" , methods=["POST"])
def decrease_cart_quantity(cart_item_id):
    if "user_id" not in session:
         return redirect(url_for("auth.login"))
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""select quantity from cart_items where user_id = %s and id = %s""" , (session["user_id"],cart_item_id))

    item = cursor.fetchone()

    if item:
        if item[0] > 1 :
            cursor.execute("""update cart_items set quantity = quantity - 1 where user_id = %s and id = %s """ ,(session["user_id"],cart_item_id))
    

        else:
            cursor.execute(
                "DELETE FROM cart_items "
                "WHERE id = %s AND user_id = %s",
                (cart_item_id, session["user_id"])
            )
        db.commit()
        cursor.close()
        db.close()    

    return redirect(url_for("auth.cart"))

###############################################################################################################################

@auth_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT ci.quantity,
                   mi.id AS menu_item_id,
                   mi.name,
                   mi.price,
                   mi.restaurant_id,
                   mi.is_available,
                   (ci.quantity * mi.price) AS subtotal
            FROM cart_items ci
            JOIN menu_items mi ON ci.menu_item_id = mi.id
            WHERE ci.user_id = %s
            """,
            (session["user_id"],)
        )

        items = cursor.fetchall()

        if not items:
            return redirect(url_for("auth.cart"))

        if any(not item["is_available"] for item in items):
            return "A food item in your cart is unavailable.", 400

        restaurant_ids = {item["restaurant_id"] for item in items}

        if len(restaurant_ids) != 1:
            return "Please order from one restaurant at a time.", 400

        subtotal = sum(item["subtotal"] for item in items)
        delivery_fee = 30
        tax_amount = 0
        discount_amount = 0
        total = subtotal + delivery_fee + tax_amount - discount_amount

        if request.method == "GET":
            return render_template(
                "checkout.html",
                items=items,
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                total=total
            )

        address = request.form.get("delivery_address", "").strip()

        if not address:
            return "Please enter a delivery address.", 400

        restaurant_id = items[0]["restaurant_id"]

        cursor.execute(
            """
            INSERT INTO orders
            (user_id, restaurant_id, delivery_address, status,
             subtotal, delivery_fee, tax_amount, discount_amount,
             total_amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                restaurant_id,
                address,
                "placed",
                subtotal,
                delivery_fee,
                tax_amount,
                discount_amount,
                total
            )
        )

        order_id = cursor.lastrowid

        for item in items:
            cursor.execute(
                """
                INSERT INTO order_items
                (order_id, menu_item_id, item_name, quantity,
                 unit_price, subtotal)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    order_id,
                    item["menu_item_id"],
                    item["name"],
                    item["quantity"],
                    item["price"],
                    item["subtotal"]
                )
            )

        cursor.execute(
            "DELETE FROM cart_items WHERE user_id = %s",
            (session["user_id"],)
        )

        db.commit()

        return render_template(
            "order_success.html",
            order_id=order_id,
            total=total
        )

    except Exception:
        db.rollback()
        raise

    finally:
        cursor.close()
        db.close()

###############################################################################################################################


@auth_bp.route("/my-orders")
def my_orders():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT o.id, r.name AS restaurant_name,
                   o.status, o.total_amount, o.created_at
            FROM orders o
            JOIN restaurants r ON o.restaurant_id = r.id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
            """
            ,
            (session["user_id"],)
        )

        orders = cursor.fetchall()

    finally:
        cursor.close()
        db.close()

    return render_template("my_orders.html" , orders=orders)


###############################################################################################################################

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
