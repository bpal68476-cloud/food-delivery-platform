
from flask import Blueprint, session, url_for, redirect, render_template
from db import get_db_connection

restaurant_bp = Blueprint("restaurant", __name__)

#############################################################################################################################

@restaurant_bp.route("/restaurant-dashboard")
def restaurant_dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "restaurant":
        return redirect(url_for("auth.home"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                o.id AS order_id,
                r.name AS restaurant_name,
                o.status,
                o.total_amount,
                o.created_at
            FROM orders o
            JOIN restaurants r ON o.restaurant_id = r.id
            WHERE r.owner_id = %s
            ORDER BY o.created_at DESC
            """,
            (session["user_id"],)
        )

        orders = cursor.fetchall()

    finally:
        cursor.close()
        db.close()

    return render_template("restaurant_dashboard.html", orders=orders)

#############################################################################################################################

@restaurant_bp.route(
    "/restaurant/orders/<int:order_id>/accept",
    methods=["POST"]
)
def accept_order(order_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "restaurant":
        return redirect(url_for("auth.home"))

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            UPDATE orders o
            JOIN restaurants r ON o.restaurant_id = r.id
            SET o.status = 'accepted'
            WHERE o.id = %s
              AND r.owner_id = %s
              AND o.status = 'placed'
            """,
            (order_id, session["user_id"])
        )
        db.commit()

    finally:
        cursor.close()
        db.close()

    return redirect(url_for("restaurant.restaurant_dashboard"))

#############################################################################################################################

@restaurant_bp.route(
    "/restaurant/orders/<int:order_id>/reject",
    methods=["POST"]
)
def reject_order(order_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "restaurant":
        return redirect(url_for("auth.home"))

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            UPDATE orders o
            JOIN restaurants r ON o.restaurant_id = r.id
            SET o.status = 'cancelled'
            WHERE o.id = %s
              AND r.owner_id = %s
              AND o.status = 'placed'
            """,
            (order_id, session["user_id"])
        )
        db.commit()

    finally:
        cursor.close()
        db.close()

    return redirect(url_for("restaurant.restaurant_dashboard"))


#############################################################################################################################


@restaurant_bp.route(
    "/restaurant/orders/<int:order_id>/prepare",
    methods=["POST"]
)
def prepare_order(order_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "restaurant":
        return redirect(url_for("auth.home"))

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            UPDATE orders o
            JOIN restaurants r ON o.restaurant_id = r.id
            SET o.status = 'prepared'
            WHERE o.id = %s
              AND r.owner_id = %s
              AND o.status = 'accepted'
            """,
            (order_id, session["user_id"])
        )
        db.commit()

    finally:
        cursor.close()
        db.close()

    return redirect(url_for("restaurant.restaurant_dashboard"))
