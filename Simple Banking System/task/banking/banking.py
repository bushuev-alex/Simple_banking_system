import random
import sqlite3

TABLE_CARDS = 'card'
TABLE_COLUMNS = """id INTEGER PRIMARY KEY, 
                    number TEXT, 
                    pin TEXT, 
                    balance INTEGER DEFAULT 0"""
SQL_NAME = 'card.s3db'


class SqlData:

    def __init__(self, sql_filename):
        self.connection = sqlite3.connect(sql_filename)
        self.cursor = self.connection.cursor()

    def create_table(self, table_name, table_columns):
        sql_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({table_columns});"
        self.cursor.execute(sql_query)
        self.connection.commit()

    def delete_row(self, table_name, column, value_to_compare):
        sql_query = f"DELETE FROM {table_name} WHERE {column}={value_to_compare};"
        self.cursor.execute(sql_query)
        self.connection.commit()

    def close_sql(self):
        self.connection.close()

    def fetch_one_by_card_number(self, table_name, card_number):
        sql_query = f"""SELECT * from {table_name} WHERE number={card_number}"""
        self.cursor.execute(sql_query)
        return self.cursor.fetchone()

    def insert_into(self, table_name, column_names, values):
        sql_query = f"""INSERT OR REPLACE INTO {table_name} {column_names} VALUES {values};"""
        self.cursor.execute(sql_query)
        self.connection.commit()

    def update_table(self, table_name, value_to_add, column, value_to_compare):
        sql_query = f"""UPDATE {table_name} SET balance={value_to_add} WHERE {column}={value_to_compare};"""
        self.cursor.execute(sql_query)
        self.connection.commit()


sql_data = SqlData(SQL_NAME)
sql_data.create_table(TABLE_CARDS, TABLE_COLUMNS)


def user_choice():
    return input()


class Account:

    def __init__(self, iin, balance):
        self.id = 1
        self.iin = iin
        self.customer_account_number = None
        self.check_sum = None
        self.card_number = None
        self.pin = None
        self.store = dict()
        self.balance = balance

    def caa_generation(self):
        self.customer_account_number = ''
        for i in range(9):
            self.customer_account_number += str(random.randint(0, 9))
        self.customer_account_number = int(self.customer_account_number)

    def luhn_algorithm(self, card_number_to_check):
        for m in range(0, len(card_number_to_check), 2):
            if card_number_to_check[m] * 2 < 9:
                card_number_to_check[m] = card_number_to_check[m] * 2
            else:
                card_number_to_check[m] = (card_number_to_check[m] * 2) - 9
        return sum(card_number_to_check)

    def card_number_generation(self):
        #  issuer_identification_number  + customer_account_number
        iin_caa = f'{self.iin}' + f'{self.customer_account_number}'

        # make list of int from above
        list_iin_caa = [int(x) for x in iin_caa]

        # Luhn algorithm
        sum_iin_caa = self.luhn_algorithm(list_iin_caa)

        # search for checksum
        self.check_sum = 0
        while (sum_iin_caa + self.check_sum) % 10 != 0:
            self.check_sum += 1
        self.card_number = f'{self.iin}' + f'{self.customer_account_number}' + f'{self.check_sum}'

    def pin_generation(self):
        self.pin = ''
        for j in range(4):
            self.pin += str(random.randint(0, 9))

    def create_an_account(self):
        random.seed()
        self.caa_generation()
        self.card_number_generation()
        self.pin_generation()
        print('Your card has been created')
        print('Your card number:')
        print(int(self.card_number))
        print('Your card PIN:')
        print(int(self.pin))
        sql_data.insert_into('card', '(id, number, pin, balance)', f'({self.id}, {self.card_number}, {self.pin}, {self.balance})')
        self.id += 1

    def add_income(self):
        self.balance += int(input('Enter income:\n'))
        sql_data.update_table('card', self.balance, 'number', self.card_number)
        select_card_info_from_db = sql_data.fetch_one_by_card_number('card', self.card_number)
        self.balance = select_card_info_from_db[3]
        print('Income was added!')

    def transfer_balance(self):
        print('Transfer')
        print('Enter card number:\n')
        card_number_to_transfer = input()
        #  check card_number accuracy:
        luhn_algo_result = self.luhn_algorithm([int(x) for x in card_number_to_transfer[:-1]])
        if (luhn_algo_result + int(card_number_to_transfer[-1])) % 10 != 0:
            print('Probably you made a mistake in the card number. Please try again!')
        else:
            card_number_to_transfer_info = sql_data.fetch_one_by_card_number('card', card_number_to_transfer)
            if card_number_to_transfer_info is None:
                print('Such a card does not exist.')
            else:
                amount_money_to_transfer = int(input('Enter how much money you want to transfer:\n'))
                if amount_money_to_transfer > self.balance:
                    print('Not enough money!')
                else:
                    #  update current card balance (-)
                    sql_data.update_table('card', (self.balance-amount_money_to_transfer), 'number', self.card_number)
                    select_card_info_from_db = sql_data.fetch_one_by_card_number('card', self.card_number)
                    self.balance = select_card_info_from_db[3]
                    #  change balance of card to transfer (+)
                    select_card_to_transfer_info_from_db = sql_data.fetch_one_by_card_number('card', card_number_to_transfer)
                    balance_after_transfer = select_card_to_transfer_info_from_db[3] + amount_money_to_transfer
                    sql_data.update_table('card', balance_after_transfer, 'number', card_number_to_transfer)
                    print('Success!')

    def log_into_account(self):
        print('Enter your card number:')
        self.card_number = input()
        print('Enter your PIN:')
        self.pin = input()
        #  select_card_info_from_db
        fetched_card_info_from_db = sql_data.fetch_one_by_card_number('card', self.card_number)

        # Check stored account details with new input data
        try:
            if fetched_card_info_from_db[1] != self.card_number or fetched_card_info_from_db[2] != self.pin:
                print('Wrong card number or PIN!')
                return True
        except TypeError:  # None means there is no data select_card_info_from_db(i.e. card_number) in the db
            print('Wrong card number or PIN!')
            return True
        else:
            self.id = fetched_card_info_from_db[0]
            self.balance = fetched_card_info_from_db[3]
            print('You have successfully logged in!')
            while True:
                #  Options_cycle after successful login
                print('1. Balance')
                print('2. Add income')
                print('3. Do transfer')
                print('4. Close account')
                print('5. Log out')
                print('0. Exit')
                after_log_choice = user_choice()
                if after_log_choice == '0':
                    return False
                elif after_log_choice == '1':
                    print('Balance:', fetched_card_info_from_db[3])
                elif after_log_choice == '2':
                    self.add_income()
                elif after_log_choice == '3':
                    self.transfer_balance()
                elif after_log_choice == '4':
                    sql_data.delete_row('card', 'number', self.card_number)
                    print('The account has been closed!')
                    return True
                elif after_log_choice == '5':
                    print('You have successfully logged out!')
                    return True


new_user = Account(400000, 0)


def main_cycle():
    while True:  # Main cycle
        print('1. Create an account')
        print('2. Log into account')
        print('0. Exit')
        choice = user_choice()
        if choice == '0':
            print('Bye!')
            break
        elif choice == '1':
            new_user.create_an_account()
        elif choice == '2':
            if not new_user.log_into_account():
                print('Bye!')
                break
            else:
                continue


main_cycle()
