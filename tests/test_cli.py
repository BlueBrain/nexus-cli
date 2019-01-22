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
    assert_command_returns_exist_code("nexus profiles create foo987 https://bbp-nexus.epfl.ch/staging", 0)
    assert_command_returns_exist_code("nexus profiles select foo987", 0)
    assert_command_returns_exist_code("nexus profiles list", 0)
    assert_command_returns_exist_code("nexus profiles delete foo987", 0)

