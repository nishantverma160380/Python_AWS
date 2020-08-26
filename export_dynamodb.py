#!/usr/bin/env python3

import boto3
import os
import pickle
import traceback
import fire

REGION = 'eu-west-1'
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
TEMP_FILE_PATH = os.path.join(DIR_PATH, 'dynamo.pickle')


def _get_env_table_name(table: str, env: str):
    return table.format(ENV=env)


def _get_dynamodb():
    return boto3.resource('dynamodb', region_name=REGION)


def pull(table: str, env: str = ""):
    """
    Get all the items from DynamoDB table to clone and save as pickle file
    :param table: Table name from which it will be cloned
    :param env: Environment name which will be replaced in table name
    :return:
    """
    if env:
        table = _get_env_table_name(table, env)
    dynamodb = _get_dynamodb()
    print(env)
    print(table)
    boto3_table = dynamodb.Table(table)
    response = boto3_table.scan()
    data = response['Items']

    while response.get('LastEvaluatedKey', False):
        response = boto3_table.scan()
        data.extend(response['Items'])

    with open(TEMP_FILE_PATH, "wb+") as pickle_out:
        pickle.dump(data, pickle_out)


def push(table: str, env: str = "", clean: bool = True):
    """
    Reads pickle file with item data and update the table
    :param table: Table name from which it will be cloned
    :param env: Environment name which will be replaced in table name
    :param clean: Defaults to True. Deletes pickle file if true
    :return:
    """
    if env:
        table = _get_env_table_name(table, env)

    dynamodb = _get_dynamodb()
    boto3_table = dynamodb.Table(table)

    with open(TEMP_FILE_PATH, "rb+") as pickle_in:
        dynamodb_items = pickle.load(pickle_in)

    for item in dynamodb_items:
        boto3_table.put_item(Item=item)

    clean_up() if clean else None


def clean_up():
    try:
        os.remove(TEMP_FILE_PATH)
    except FileNotFoundError:
        print('Nothing to clean')
    except Exception:
        print(traceback.print_exc())


if __name__ == '__main__':
    try:
        fire.Fire({
            'push': push,
            'pull': pull,
            'clean': clean_up
        })
    except Exception:
        print(traceback.print_exc())