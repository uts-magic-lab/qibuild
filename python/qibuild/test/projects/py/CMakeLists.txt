## Copyright (c) 2012-2016 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.
cmake_minimum_required(VERSION 2.8)
project(py)

find_package(qibuild)

add_definitions("-DQI_VIRTUALENV_PATH=\"${QI_VIRTUALENV_PATH}\"")

qi_create_bin(py_test "main.cpp")
