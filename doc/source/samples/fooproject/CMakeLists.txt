## Copyright (c) 2012-2016 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

cmake_minimum_required(VERSION 2.8)
project(fooproject)
find_package(qibuild)

# Add a subdirectory containing the foo library
add_subdirectory(libfoo)


# Use it in the bar project.
qi_create_bin(bar main.cpp)
qi_use_lib(bar foo)
