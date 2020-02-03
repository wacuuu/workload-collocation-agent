# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import argparse
import time

import mysql.connector


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s', '--host', dest="host",
        help="Host", default='127.0.0.1', required=True)
    parser.add_argument(
        '-u', '--user', dest="user",
        help="User", default='testuser')
    parser.add_argument(
        '-p', '--password', dest="password",
        help="Password", default='testpassword')
    parser.add_argument(
        '-d', '--database', dest="database",
        help="Database", default='')
    parser.add_argument(
        '-i', '--interval', dest="interval",
        help="Interval in seconds", default='1')

    command = "show global status " \
              "where Variable_name = 'Com_commit' " \
              "or Variable_name =  'Com_rollback';"

    args = parser.parse_args()

    interval = int(args.interval)

    while True:
        try:
            mydb = mysql.connector.connect(
                host=args.host,
                user=args.user,
                passwd=args.password,
                database=args.database
            )

            break  # Only triggered if successful connect to database
        except mysql.connector.Error as err:
            print(err)
        else:
            mydb.close()
            exit(1)

    cursor = mydb.cursor()

    cursor.execute(command)
    result = cursor.fetchall()
    before = int(result[0][1]) + int(result[1][1])

    while True:
        cursor.execute(command)
        result = cursor.fetchall()

        # Com_commit + Com_rollback
        now = int(result[0][1]) + int(result[1][1])
        delta = now - before
        before = now
        tpm = delta * 60 / interval
        print("TPM: %f" % tpm)

        time.sleep(interval)


if __name__ == '__main__':
    main()
