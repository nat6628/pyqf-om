import io
import sqlite3

import pandas as pd
import streamlit as st
import time

from orderpush.models import Order, CancelOrder, ModifyOrder

st.title("Market")


def get_data_symbol():
    conn = sqlite3.connect("database.db")
    data = pd.read_sql_query("SELECT * FROM symbol", conn)
    data = data.rename(
        columns={
            "symbol": "Symbol",
            "close": "Close",
            "limitUp": "Limit Up",
            "limitDown": "Limit Down",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "lastPrice": "Last Price",
            "volume": "Volume",
        }
    )
    numeric_cols = [
        "Close",
        "Limit Up",
        "Limit Down",
        "Open",
        "High",
        "Low",
        "Last Price",
        "Volume",
    ]
    data[numeric_cols] = data[numeric_cols].map(lambda x: "{:.2f}".format(x))
    conn.close()
    return data


def get_pending_orders():
    conn = sqlite3.connect("database.db")
    data = pd.read_sql_query(
        "SELECT clOrdID, symbol, side, ordType, price, quantity, executedQuantity, lastExecutedQuantity, lastExecutedPrice, openQuantity FROM pending_order",
        conn,
    )
    data = data.rename(
        columns={
            "clOrdID": "Order ID",
            "symbol": "Symbol",
            "side": "Side",
            "ordType": "Order Type",
            "price": "Price",
            "quantity": "Quantity",
            "executedQuantity": "Executed Quantity",
            "lastExecutedQuantity": "Last Executed Quantity",
            "lastExecutedPrice": "Last Executed Price",
            "openQuantity": "Open Quantity",
        }
    )
    mumeric_cols = [
        "Price",
        "Quantity",
        "Executed Quantity",
        "Last Executed Quantity",
        "Last Executed Price",
        "Open Quantity",
    ]
    data[mumeric_cols] = data[mumeric_cols].map(lambda x: "{:.2f}".format(x))
    conn.close()
    return data


def get_order_history():
    conn = sqlite3.connect("database.db")
    data = pd.read_sql_query(
        "SELECT clOrdID, symbol, side, ordType, price, quantity, executedQuantity, lastExecutedQuantity, lastExecutedPrice, status FROM order_history",
        conn,
    )
    data = data.rename(
        columns={
            "clOrdID": "Order ID",
            "symbol": "Symbol",
            "side": "Side",
            "ordType": "Order Type",
            "price": "Price",
            "quantity": "Quantity",
            "executedQuantity": "Executed Quantity",
            "lastExecutedQuantity": "Last Executed Quantity",
            "lastExecutedPrice": "Last Executed Price",
            "status": "Status",
        }
    )
    mumeric_cols = [
        "Price",
        "Quantity",
        "Executed Quantity",
        "Last Executed Quantity",
        "Last Executed Price",
    ]
    data[mumeric_cols] = data[mumeric_cols].map(lambda x: "{:.2f}".format(x))
    conn.close()
    return data


def find_symbol(symbol):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM symbol WHERE symbol = ?", (symbol,))
    row = cursor.fetchone()
    conn.close()
    return row

def find_order(clOrdID):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pending_order WHERE clOrdID = ?", (clOrdID,))
    row = cursor.fetchone()
    conn.close()
    return row

def is_number(n):
    try:
        float(n)
        return True
    except ValueError:
        return False


def main(file: io.TextIOWrapper):
    clOrdID = 1

    page = st.sidebar.selectbox("Choose a page", ["Home", "Orders"])
    if page == "Home":
        df = pd.DataFrame(get_data_symbol())
        st.table(df)
        with st.sidebar.form(key="my_form"):
            symbols = df["Symbol"].tolist()

            symbol = st.selectbox("Symbol", symbols)
            price = st.text_input(label="Price")
            quantity = st.text_input(label="Quantity")
            side = st.selectbox("Side", ["BUY", "SELL"])
            submit_button = st.form_submit_button(label="Submit")
            symbol_data = find_symbol(symbol)
            if submit_button:
                if symbol == "" or price == "" or quantity == "":
                    st.error("Error: All fields must be filled in.")
                elif not is_number(price) or not is_number(quantity):
                    st.error("Error: Price and Quantity must be numbers.")
                elif symbol_data is None:
                    st.error("Error: Symbol not found.")
                elif symbol_data[2] < float(price) or symbol_data[3] > float(price):
                    st.error("Error: Price is out of range.")
                else:
                    side_number = '1' if side == "BUY" else '2' if side == "SELL" else 0
                    print(side)
                    order = Order('NEW', str(clOrdID), symbol, price, side_number, quantity)
                    print(order)
                    file.write(order.to_csv() + "\n")
                    file.flush()
                    success_message = st.sidebar.empty()
                    success_message.success('New order successfully placed!')
                    time.sleep(5)
                    success_message.empty()
                    clOrdID += 1

    elif page == "Orders":
        order_page = st.sidebar.selectbox(
            "Order Page", ["Pending Orders", "Order History"], key="order_page"
        )
        if order_page == "Pending Orders":
            df = pd.DataFrame(get_pending_orders())
            st.table(df)
            action = st.sidebar.selectbox("Action", ["Cancel", "Modify"])
            if action == "Modify":
                if 'order_modified' in st.session_state and st.session_state.order_modified:
                    success_message = st.sidebar.empty()
                    success_message.success('Order successfully modified!')
                    del st.session_state.order_modified

                with st.sidebar.form(key="modify_form"):
                    symbols = df["Symbol"].tolist()
                    order_ids = df["Order ID"].tolist()
                    selected_order_id = st.selectbox(
                        "Order ID",
                        order_ids,
                        format_func=lambda x: x if x else "No orders available",
                    )
                    if not order_ids:  # If the list is empty, disable the form
                        st.warning("No pending orders available to modify.")
                        st.stop()
                    new_symbol = st.selectbox("New symbol", symbols)
                    new_side = st.selectbox("New side", ["BUY", "SELL"])
                    new_price = st.text_input("New price")
                    new_quantity = st.text_input("New quantity")
                    new_symbol_data = find_symbol(new_symbol)
                    if st.form_submit_button("Submit"):
                        if new_symbol == "" or new_side == "" or new_price == "" or new_quantity == "":
                            st.error("Error: All fields must be filled in.")
                        elif not is_number(new_price) or not is_number(new_quantity):
                            st.error("Error: Price and Quantity must be numbers.")
                        elif new_symbol_data is None:
                            st.error("Error: Symbol not found.")
                        elif new_symbol_data[2] < float(new_price) or new_symbol_data[3] > float(new_price):
                            st.error("Error: Price is out of range.")
                        else:
                            order_data = find_order(selected_order_id)
                            side_number = '1' if new_side == "BUY" else '2' if new_side == "SELL" else '0'
                            modify_order = ModifyOrder('MODIFY', str(selected_order_id), new_symbol, new_price, side_number, new_quantity, '0')
                            print(modify_order)
                            file.write(modify_order.to_csv() + "\n")
                            file.flush()
                            st.session_state.order_modified = True
                            st.experimental_rerun()

            if action == "Cancel":
                if 'order_canceled' in st.session_state and st.session_state.order_canceled:
                    success_message = st.sidebar.empty()
                    success_message.success('Order successfully canceled!')
                    del st.session_state.order_canceled

                with st.sidebar.form(key="order_form"):
                    order_ids = df["Order ID"].tolist()
                    selected_order_id = st.selectbox(
                        "Order ID",
                        order_ids,
                        format_func=lambda x: x if x else "No orders available",
                    )
                    if not order_ids:  # If the list is empty, show warning and stop
                        st.warning("No pending orders available to cancel.")
                        st.stop()

                    # The rest of your form and logic here
                    if st.form_submit_button("Submit"):
                        order_data = find_order(selected_order_id)
                        print(order_data[4])
                        side_number = '1' if order_data[4] == "BUY" else '2' if order_data[4] == "SELL" else '0'
                        cancel_order = CancelOrder('CANCEL', str(order_data[0]), order_data[1], side_number)
                        print(cancel_order)
                        file.write(cancel_order.to_csv() + "\n")
                        file.flush()
                        st.session_state.order_canceled = True
                        st.experimental_rerun()

        elif order_page == "Order History":
            df = pd.DataFrame(get_order_history())
            st.table(df)


if __name__ == "__main__":
    with open("order.csv", "a+") as f:
        main(f)
