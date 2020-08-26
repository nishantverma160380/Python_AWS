#!/usr/bin/env python3

import boto3
import urllib3
import yaml
import pickle
import os
import sys
import fire

REGION = 'eu-west-1'
dir_path = os.path.dirname(os.path.realpath(__file__))


def _get_lambda():
    return boto3.client('lambda', region_name=REGION)


def load_env_config():
    try:
        with open(os.path.join(sys.path[0], os.path.join(dir_path, 'config/config.yml')), 'rb') as handle:
            lambda_metadata = yaml.safe_load(handle)
            return lambda_metadata if lambda_metadata else {}
    except FileNotFoundError as fnfe:
        print(fnfe)


def get_function_alias_data(function_name, env):
    """
    Get the lambda function alias data
    :param function_name: Name of the lambda function
    :param env: Environment name from which the lambda alias required
    :return:
    """
    lambda_client = _get_lambda()
    function_name = function_name.format(ENV=f'{env}')
    function_alias_data = {
        'FunctionName': f'{function_name}',
        'Name': f'{env}'
    }
    function_alias_data = lambda_client.get_alias(**function_alias_data)
    return function_alias_data


def pull(function_name: str, env: str):
    """
    Get the lambda function configuration and package to clone and saved in a pickle file
    :param function_name: Name of the lambda function to be cloned
    :param env: Environment name from which the lambda to be cloned
    :return:
    """
    try:
        lambda_client = _get_lambda()
        function_name = function_name.format(ENV=f'{env}')
        function_alias_data = get_function_alias_data(function_name, f'{env}')
        function_data = lambda_client.get_function(
            FunctionName=f"{function_alias_data['AliasArn']}",
            Qualifier=f'{env}'
        )
        function_data.pop("ResponseMetadata")
        code_url = function_data.pop("Code")["Location"]
        http = urllib3.PoolManager()
        response = http.request("GET", code_url)
        if not 200 <= response.status < 300:
            raise Exception(f"Failed to download function code: {response}")
        function_code = response.data
        new_function_data = {
            n: v
            for n, v in function_data["Configuration"].items()
            if n in (
                "Runtime",
                "Role",
                "Handler",
                "Description",
                "Timeout",
                "MemorySize",
                "Publish",
                "Environment",
            )
        }
        # Provide function code zip data
        new_function_data["Code"] = {"ZipFile": function_code}
        with open(os.path.join(dir_path, "dict.pickle"), "wb+") as pickle_out:
            pickle.dump(new_function_data, pickle_out)
    except Exception as e:
        print(e)


def push(function_name, env, lambda_bucket):
    """
    Get the lambda function configuration and package from the pickle file and clone it to the destination environment
    :param function_name: Name of the lambda function cloned
    :param env: Environment name where the lambda is cloned
    :param lambda_bucket: S3 Bucket where the cloned package is saved
    :return:
    """
    try:
        lambda_client = _get_lambda()
        function_name = function_name.format(ENV=f'{env}')
        function_alias_data = get_function_alias_data(function_name, f'{env}')
        function_data = lambda_client.get_function(
            FunctionName=f"{function_alias_data['AliasArn']}",
            Qualifier=f'{env}'
        )
        ian_role = function_data['Configuration']['Role']

        with open(os.path.join(dir_path, "dict.pickle"), "rb+") as pickle_in:
            new_function_data = pickle.load(pickle_in)
        new_function_data['FunctionName'] = f'{function_name}'
        new_function_data['Environment']['Variables']['STAGE'] = f'{env.upper()}'
        new_function_data['Role'] = f'{ian_role}'
        s3_resource = boto3.resource('s3')
        s3_resource.Object(lambda_bucket, f'{function_name}.zip')\
            .put(Body=new_function_data["Code"]["ZipFile"])

        update_code_response = lambda_client.update_function_code(
            FunctionName=f'{function_name}',
            S3Bucket=lambda_bucket,
            S3Key=f'{function_name}.zip'
        )
        if 'ResponseMetadata' in update_code_response and \
                update_code_response['ResponseMetadata']['HTTPStatusCode'] == 200:
            new_function_data.pop("Code")
            update_function_response = lambda_client.update_function_configuration(**new_function_data)
            if 'ResponseMetadata' in update_function_response and \
                    update_function_response['ResponseMetadata']['HTTPStatusCode'] == 200:
                publish_version_response = lambda_client.publish_version(
                    FunctionName=f"{update_code_response['FunctionArn']}"
                )
                if 'ResponseMetadata' in publish_version_response and \
                        publish_version_response['ResponseMetadata']['HTTPStatusCode'] == 201:

                    update_alias_response = lambda_client.update_alias(
                        FunctionName=f"{publish_version_response['FunctionName']}",
                        Name=f'{env}',
                        FunctionVersion=f"{publish_version_response['Version']}"
                    )
                    if 'ResponseMetadata' in update_alias_response and \
                            update_alias_response['ResponseMetadata']['HTTPStatusCode'] == 200:
                        print(f'Lambda {function_name} cloned on {env} successfully')
        else:
            print(f'Lambda {function_name} cloning on {env} failed')
            raise ValueError(f'Unable to clone Lambda {function_name} on {env}')
        cleanup()
    except Exception as e:
        print(e)


def cleanup():
    try:
        with open(os.path.join(dir_path, "dict.pickle"), "wb+") as pickle_out:
            new_function_data = {}
            pickle.dump(new_function_data, pickle_out)
            pickle_out.flush()
    except Exception as e:
        print(e)


if __name__ == '__main__':
    fire.Fire({
        'push': push,
        'pull': pull,
        'cleanup': cleanup
    })
