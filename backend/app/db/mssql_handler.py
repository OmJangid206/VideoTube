"""
mssql_handler.py

This module provides a MSSQLConnector class that facilitates reading from and
writing records to an MS SQL Server.
"""

import pymssql

class MSSQLConnector:
    """
    A class representing a connection to an MS SQL Server and associated operations.

    Methods:
        __init__(self, server, port, user, passwd, database): 
            Initializes the MSSQLConnector instance.
        connect(self): Establishes a connection to the MS SQL Server.
        disconnect(self): Closes the connection and cursor to the MS SQL Server.
        select(self, query): Executes a SELECT query and returns the results.
        update_single_row(self, data, query): Executes an UPDATE query to modify a single row.
    """

    def __init__(self, server, port, user, password, database):
        """
        Initializes the MSSQLConnector with connection details for the MS SQL Server.
        
        Args:
            server (str): The server address of the MS SQL Server.
            port (int): The port number to connect to the server.
            user (str): The username for authentication.
            password (str): The password for authentication.
            database (str): The database name to connect to.
        """
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None

    def connect(self) -> int:
        """
        Establishes a connection to the MS SQL Server using the provided credentials.

        Returns:
            int: Status code indicating the result of the connection attempt. 
                 200 for success, other codes for failures.
        """
        status_code = 200

        print("MSSQL Server connection status:")

        try:
            self.connection = pymssql.connect(
                server=self.server,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print("Status: 200")
            print("Message: Connection active")

            self.cursor = self.connection.cursor()

        except pymssql.Error as err:
            status_code = err.args[0][0]
            message = f"{err.__class__.__name__} - {err.args[0][1].decode('UTF-8')}"
            print(f"Status: {status_code}")
            print(f"message: {message}")

        except Exception as err:
            status_code = 500
            message = f"Unknown error occured - {str(err)}"

        return status_code

    def disconnect(self) -> None:

        """
        Closes the connection to the MS SQL Server and any active cursors.
        """
        print("MSSQL Server Disconnected status:")

        if self.cursor:
            self.cursor.close()
            print("Cursor closed.")
        else:
            print("No active cursor to close.")

        if self.connection:
            self.connection.close()
            print("Connection closed.")
        else:
            print("No active connection to close.")

    def select(self, query) -> tuple:

        """
        Executes a SELECT query on the MS SQL Server database.

        Args:
            query (str): The SELECT query to be executed.

        Returns:
            tuple: A tuple containing the status code and the records (or None if no records).
                   Status code 200 for success, 204 for no records, or error codes for failure.
        """

        records = None
        status_code = 200

        try:
            cursor = self.connection.cursor(as_dict=True)
            cursor.execute(query)
            records = cursor.fetchall()
            if not records:
                status_code = 204

        except pymssql.Error as err:
            status_code = err.args[0]
            message = f"{err.__class__.__name__} - {err.args[1].decode('UTF-8')}"
            print(f"status: {status_code}")
            print(f"message: {message}")

        except Exception as err:
            status_code = 500
            message = f"Unknown error occured - {str(err)}"
            print(f"status: {status_code}")
            print(f"message: {message}")

        return status_code, records

    def update_single_row(self, data, query) -> int:
        """
        Executes an UPDATE query to modify a single row in the database.

        Args:
            data (tuple): The data to be updated.
            query (str): The UPDATE query.

        Returns:
            int: Status code indicating success (200) or failure (error codes).
        """

        status_code = 200

        try:
            self.cursor.execute(query, data)
            self.connection.commit()

        except pymssql.Error as err:
            status_code = err.args[0]
            message = f"{err.__class__.__name__} - {err.args[1].decode('UTF-8')}"
            print(f"status: {status_code}")
            print(f"message: {message}")

        except Exception as err:
            status_code = 500
            message = f"Unknown error occured - {str(err)}"
            print(f"status: {status_code}")
            print(f"message: {message}")

        return status_code

# import os
# from dotenv import load_dotenv, dotenv_values
# from db.mssql_handler import MSSQLConnector

# load_dotenv()

# SERVER=os.environ["SERVER"]
# PORT=os.environ["PORT"]
# USER=os.environ["USER"]
# PASSWORD=os.environ["PASSWORD"]
# DATABASE=os.environ["DATABASE"]


# def mssql_connect():
#     try:
#         mssql_connector = MSSQLConnector(
#             server=SERVER,
#             port=PORT,
#             user=USER,
#             password=PASSWORD,
#             database=DATABASE
#         )

#         status_code = mssql_connector.connect()
#         if status_code==200:
#             print(f"MSSQL Connection established successfully with database {DATABASE}.")
#             return mssql_connector
#         else:
#             print(f"Failed to establish MSSQL connection.")
#             return None

#     except Exception as err:
#         print(f"Exception occurred during connection establishment: {str(err)}")
#         return None

# def mssql_disconnect(mssql_connector):
#     mssql_connector.disconnect()
#     print(f"MSSQL Disconnected sucessfully.")

# mssql_connector = mssql_connect()
# mssql_disconnect(mssql_connector)
