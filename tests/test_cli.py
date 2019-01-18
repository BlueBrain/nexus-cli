import pytest
import subprocess


def assert_command_returns_exist_code(command, expected_exit_code):
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()
    if p_status != 0:
        print("Command output : ", output)
        print("Command exit status/return code : ", p_status)
    assert p_status == expected_exit_code
    return output


def test_nexus_help():
    assert_command_returns_exist_code("nexus --help", 0)


def test_nexus_deployments_add():
    assert_command_returns_exist_code("nexus deployments --add foo --url https://bbp-nexus.epfl.ch/staging", 0)
    assert_command_returns_exist_code("nexus deployments --select foo", 0)
    assert_command_returns_exist_code("nexus deployments --list", 0)
    assert_command_returns_exist_code("nexus deployments --list --count", 0)
    assert_command_returns_exist_code("nexus deployments --remove foo", 0)


def test_nexus_acls_list():
    assert_command_returns_exist_code("nexus deployments --add foo --url https://bbp-nexus.epfl.ch/staging", 0)
    assert_command_returns_exist_code("nexus deployments --select foo", 0)
    assert_command_returns_exist_code("nexus acls --list", 0)
    assert_command_returns_exist_code("nexus deployments --remove foo", 0)


def test_nexus_contexts():
    assert_command_returns_exist_code("nexus deployments --add foo --url https://bbp-nexus.epfl.ch/staging", 0)
    assert_command_returns_exist_code("nexus deployments --select foo", 0)
    assert_command_returns_exist_code("nexus contexts --list", 0)
    assert_command_returns_exist_code("nexus contexts --search foo", 0)
    assert_command_returns_exist_code("nexus deployments --remove foo", 0)

def test_nexus_organizations():
    assert_command_returns_exist_code("nexus deployments --add foo --url https://bbp-nexus.epfl.ch/staging", 0)
    assert_command_returns_exist_code("nexus deployments --select foo", 0)
    assert_command_returns_exist_code("nexus orgs --list", 0)
    assert_command_returns_exist_code("nexus deployments --remove foo", 0)


def test_nexus_domains():
    assert_command_returns_exist_code("nexus deployments --add foo --url https://bbp-nexus.epfl.ch/staging", 0)
    assert_command_returns_exist_code("nexus deployments --select foo", 0)
    org_output = assert_command_returns_exist_code("nexus orgs --list --no-format", 0)
    print(org_output)
    orgs = org_output.split("\n")
    print(orgs)
    first_line = orgs[0]
    print(first_line)
    values = first_line.split(',')
    print(values)
    org_name = values[0]
    print(org_name)
    assert_command_returns_exist_code("nexus domains --list --organization %s" % random_org, 0)
    assert_command_returns_exist_code("nexus deployments --remove foo", 0)

