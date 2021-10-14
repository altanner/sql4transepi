
#~ Standard library imports
import sys
import os
import traceback
import re
from string import Template
import argparse
import pprint
import csv

#~ 3rd party imports
import pandas as pd
import psycopg2


def args_setup():

    parser = argparse.ArgumentParser(
        description="PostgreSQL DB Querier: Boots transaction data",
        epilog="Example: python pg_querier.py -d database1 -t table1 --customer 9874786793 --date 20180621 --spend")
    parser.add_argument(
        "--details", action="store_true",
        help="Provide DB and table information.")
    parser.add_argument(
        "-d", "--db", action="store",
        help="The name of the DB to query.")
    parser.add_argument(
        "--card_table", action="store",
        help="The name of the card table to query.")
    parser.add_argument(
        "--product_table", action="store",
        help="The name of the product table to query.")
    parser.add_argument(
        "--customer", action="store",
        help="Customer code to query. Format: 9874786793")
    parser.add_argument(
        "--product", action="store",
        help="Product code to query. Format: 8199922")
    parser.add_argument(
        "--date", action="store",
        help="Shop date to query. Format: YYYYMMDD")
    parser.add_argument(
        "--count", action="store_true",
        help="Return total record counts.")
    parser.add_argument(
        "--spend", action="store_true",
        help="Return total spend for the query.")
    parser.add_argument(
        "--join", action="store_true",
        help="Return card transaction items JOINed with product information.")

    args = parser.parse_args()

    return parser, args


def output_type(record_type, result):

    """Handles the type of record we want outputted,
    for example for standard queries we might want raw records.
    A count instead, we might want an integer."""

    if record_type == "*":
        print(result)
    else:
        print(result[0][0])


#~ QUERIES FUNCTIONS start =======================
def all_records_from_product(
    product,
    record_type,
    table,
    cursor,
    connection):

    sql = Template("""
        SELECT $record_type FROM $table
        WHERE ITEM_CODE = '$product';""")

    try:
        cursor.execute(sql.substitute(record_type=record_type, table=table, product=product))
        result = cursor.fetchall()
        output_type(record_type, result)
    except Exception as e:
        print(e)


def all_records_from_date(
    date,
    record_type,
    table,
    cursor,
    connection):

    sql = Template("""
        SELECT $record_type FROM $table
        WHERE DATE2 = '$date';""")

    try:
        cursor.execute(sql.substitute(record_type=record_type, table=table, date=date))
        result = cursor.fetchall()
        output_type(record_type, result)
    except Exception as e:
        print(e)


#~ CUSTOMER queries =========================
def customer_records_all(
    customer,
    record_type,
    table,
    cursor,
    connection):

    sql = Template("""
        SELECT $record_type FROM $table
        WHERE ID = '$customer';""")

    try:
        cursor.execute(sql.substitute(record_type=record_type, table=table, customer=customer))
        result = cursor.fetchall()
        output_type(record_type, result)
    except Exception as e:
        print(e)


def customer_records_for_product(
    customer,
    product,
    record_type,
    table,
    cursor,
    connection):

    sql = Template("""
        SELECT $record_type FROM $table
        WHERE ID = '$customer'
        AND ITEM_CODE = '$product';""")

    try:
        cursor.execute(sql.substitute(record_type=record_type, table=table, customer=customer, product=product))
        result = cursor.fetchall()
        output_type(record_type, result)
    except Exception as e:
        print(e)


def customer_records_from_date(
    customer,
    date,
    record_type,
    table,
    cursor,
    connection):

    sql = Template("""
        SELECT $record_type FROM $table
        WHERE DATE2 = '$date'
        AND ID = '$customer';""")

    try:
        cursor.execute(sql.substitute(record_type=record_type, table=table, customer=customer, date=date))
        result = cursor.fetchall()
        output_type(record_type, result)
    except Exception as e:
        print(e)


#~ CUSTOMER RECORDS TEMPORALLY WITH PRODUCT ======
def customer_records_for_product_from_date(
    customer,
    date,
    product,
    record_type,
    table,
    cursor,
    connection):

    sql = Template("""
        SELECT $record_type FROM $table
        WHERE ID = '$customer'
        AND DATE2 = '$date'
        AND ITEM_CODE = '$product';""")

    try:
        cursor.execute(sql.substitute(record_type=record_type, table=table, customer=customer, date=date, product=product))
        result = cursor.fetchall()
        output_type(record_type, result)
    except Exception as e:
        print(e)

#~ inter-table operations
def join_on_product_id(
    record_type,
    card_table,
    product_table,
    cursor,
    connection):

    """
    The card transaction table contains each item purchased, but without
    further product information. The product table contain information,
    and can be linked to the transaction table. So, this function takes the
    product ID numbers common to both tables and does a JOIN on them.
    """

    sql = Template("""
        SELECT $record_type FROM $card_table
        INNER JOIN $product_table
        ON $card_table.ITEM_CODE = $product_table.productid;""")

    try:
        cursor.execute(sql.substitute(
            record_type=record_type,
            card_table=card_table,
            product_table=product_table))
        result = cursor.fetchall()
        output_type(record_type, result)
    except Exception as e:
        print(e)


#~ GENERAL STATUS QUERY =====================
def db_details(
    db,
    card_table,
    product_table,
    cursor,
    connection):

    """
    Return some information about the current state of Postgres.
    """

    sql_card_column_count = Template("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name='$table';""")
    sql_card_record_count = Template("""
        SELECT COUNT(*)
        FROM $table;""")
    sql_product_column_count = Template("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name='$table';""")
    sql_product_record_count = Template("""
        SELECT COUNT(*)
        FROM $table;""")

    try:
        cursor.execute(sql_card_column_count.substitute(table=card_table))
        card_column_count = cursor.fetchall()
        cursor.execute(sql_card_record_count.substitute(table=card_table))
        card_record_count = cursor.fetchall()
        cursor.execute(sql_product_column_count.substitute(table=product_table))
        product_column_count = cursor.fetchall()
        cursor.execute(sql_product_record_count.substitute(table=product_table))
        product_record_count = cursor.fetchall()
        print(f"\nDB connection details:\n")
        pprint.pprint(connection.get_dsn_parameters())
        print(f"\nTable name:    {card_table}\nColumns:       {card_column_count[0][0]}")
        print(f"Records:       {card_record_count[0][0]}")
        print(f"\nTable name:    {product_table}\nColumns:       {product_column_count[0][0]}")
        print(f"Records:       {product_record_count[0][0]}")
        print(f"\nAbove are some details about the current DB. Please provide a query.")
        print(f"For help: python boots_PG_querier.py --help")
    except Exception as e:
        print(e)


#~ main =================================
def main():

    try:

        parser, args = args_setup()
        if len(sys.argv) < 2:
            parser.print_help(sys.stderr)
            sys.exit(1)

        #~ connect to pgsql - if no DB, see exception.
        try:
            connection = psycopg2.connect(
                database=args.db,
                user="at9362",
                password="password",
                host="127.0.0.1",
                port="5432")
            cursor = connection.cursor()
        except psycopg2.OperationalError as e:
            print(f"\n!!! {e}")
            print(f"If you would like to create a table from a CSV file, see the script csv2pg.py")
            print(f"\nTo get help: python3 pg_querier.py --help")
            sys.exit(1)

        #~ Return some DB details if no query args are given
        if args.details or not any([
            args.product,
            args.customer,
            args.date,
            args.count,
            args.spend,
            args.join]):
            db_details(
                args.db,
                args.card_table,
                args.product_table,
                cursor,
                connection)
            sys.exit(0)

        if len(sys.argv) < 6:
            parser.print_help(sys.stderr)
            print(f"\n!!! Your query request was incomplete, see above for help.")
            sys.exit(1)
        #~ if args.count is not included, SELECTs will be for all records,
        #~ flip this to COUNT or SPEND if args request
        record_type = "*"
        if args.count and args.spend:
            print(f"\n!!! Please provide just one record type (spend / count / etc).")
            sys.exit(1)
        if args.count:
            record_type = "COUNT(*)"
        if args.spend:
            record_type = "SUM(SPEND)"

    #~ three args ========================
        if args.customer and args.date and args.product:
            customer_records_for_product_from_date(
                args.customer,
                args.date,
                args.product,
                record_type,
                args.card_table,
                cursor,
                connection)
            connection.close()
            return

    #~ two args ==========================
        if args.customer and args.date:
            customer_records_from_date(
                args.customer,
                args.date,
                record_type,
                args.card_table,
                cursor,
                connection)
            connection.close()
            return

        if args.customer and args.product:
            customer_records_for_product(
                args.customer,
                args.product,
                record_type,
                args.card_table,
                cursor,
                connection)
            connection.close()
            return

    #~ one arg ===========================
        if args.customer:
            customer_records_all(
                args.customer,
                record_type,
                args.card_table,
                cursor,
                connection)
            connection.close()
            return

        if args.product:
            all_records_from_product(
                args.product,
                record_type,
                args.card_table,
                cursor,
                connection)
            connection.close()
            return

        if args.date:
            all_records_from_date(
                args.date,
                record_type,
                args.card_table,
                cursor,
                connection)
            connection.close()
            return

        if args.join:
            join_on_product_id(
                record_type,
                args.card_table,
                args.product_table,
                cursor,
                connection)
            connection.close()
            return

    except KeyboardInterrupt:
        print("OK, stopping.")
        try:
            connection.close()
        except Exception as e:
            print(e)

    except Exception:
        traceback.print_exc(file=sys.stdout)

    sys.exit(0)


if __name__ == "__main__":

    main()

