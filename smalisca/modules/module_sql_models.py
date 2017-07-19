#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# -----------------------------------------------------------------------------
# File:         modules/module_sql_models.py
# Created:      2015-01-29
# Purpose:      Model classes, methods, properties, calls as SQL objects
#
# Copyright
# -----------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2015 Victor Dorneanu <info AAET dornea DOT nu>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

"""Represent an App as SQL data"""

import re
import textwrap
import sqlite3
import sqlalchemy as sql
from sqlalchemy import ForeignKey, event
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

import smalisca.core.smalisca_config as config
from smalisca.core.smalisca_logging import log

__author__ = config.PROJECT_AUTHOR

Base = declarative_base()

import logging
logging.basicConfig()
log = logging.getLogger(__file__)
log.setLevel(logging.DEBUG)

# Tables defining relationships between entities
# Classes <-> Properties
class_properties_table = sql.Table(
    'class_properties', Base.metadata,
    sql.Column('class_id', sql.Integer, ForeignKey('classes.id')),
    sql.Column('prop_id', sql.Integer, ForeignKey('properties.id')),
    mysql_charset='utf8'
)

# Classes <-> Const Strings
class_const_strings_table = sql.Table(
    'class_const_strings', Base.metadata,
    sql.Column('class_id', sql.Integer, ForeignKey('classes.id')),
    sql.Column('const_string_id', sql.Integer, ForeignKey('const_strings.id')),
    mysql_charset='utf8'
)

# Classes <-> Methods
class_methods_table = sql.Table(
    'class_methods', Base.metadata,
    sql.Column('class_id', sql.Integer, ForeignKey('classes.id')),
    sql.Column('method_id', sql.Integer, ForeignKey('methods.id')),
    mysql_charset='utf8'
)

"""
# U N C O M M E N T    T H I S  I F  Y O U   W A N T   T O   M O N I T O R
# T I M E   E X E C U T I O N   O F   A L L   T H E   Q U E R I E S
# WARNING: This is very VERBOSE!!
#==============================================================================
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement,
                        parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())
    log.debug("Start Query: %s", statement)

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement,
                        parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    log.debug("Query Complete!")
    log.debug("Total Time: %f", total)

#==============================================================================
"""

def regexp(pattern, input):
    try:
        """
        re.I = ignore case
        re.X verbose mode, this enables to write comments inside regex expr.
        e.g: r'(.*) # some comment that will be ignored'
        """
        reg = re.compile(pattern)
    except re.error:
        #log.debug("Failed to compile the following regex's pattern >>> {0}".format(pattern))
        return False
    return reg.search(input) is not None


class SmaliClass(Base):
    """Models a Smali class

    Attributes:
        id (integer): Primary key
        class_name (str): Name of the class
        class_type (str): Type of the class (public, abstract, etc.)
        class_package (str): Name of the package the class belongs to
        depth (integer): Some path depth (not used)
        path (str): Location of file where the class has been found
        properties (list): List of properties (:class:`SmaliProperty`)
        methods (list): List of methods (:class:`SmaliMethod`)

    """
    __tablename__ = "classes"

    # Fields
    id = sql.Column(sql.Integer, primary_key=True)
    class_name = sql.Column(sql.Text(collation='utf8_general_ci'), unique=False)
    class_type = sql.Column(sql.Text(collation='utf8_general_ci'), unique=False)
    class_package = sql.Column(sql.Text(collation='utf8_general_ci'), unique=False)
    depth = sql.Column(sql.Integer)
    path = sql.Column(sql.String(255), unique=False)

    # Relationships
    properties = relationship(
        'SmaliProperty', secondary=class_properties_table)
    const_strings = relationship(
        'SmaliConstString', secondary=class_const_strings_table)
    methods = relationship(
        'SmaliMethod', secondary=class_methods_table)

    def to_string(self):
        s = """
        :: ID: %d\n
        \t[+] Name: \t%s
        \t[+] Type: \t%s
        \t[+] Depth: \t%s
        \t[+] Path: \t%s
        """ % (
            self.id, self.class_name, self.class_type,
            self.depth, self.path
        )
        return textwrap.dedent(s)

    def toDict(self):
        return {'class_name'    :   self.class_name,
                'class_type'    :   self.class_type,
                'class_depth'   :   self.depth}

    def __str__(self):
        return self.to_string()

    def __unicode__(self):
        return self.to_string()


class SmaliProperty(Base):
    """Models a Smali class property

    Attributes:
        id (integer): Primary key
        property_name (str): Name of the property
        property_type (str): Property type (e.g. Ljava/lang/String)#
        property_info (str): Additional property info (private, static, finale, etc.)
        class_name (str): The class this property belongs to

    """
    __tablename__ = "properties"

    # Fields
    id = sql.Column(sql.Integer, primary_key=True)
    property_name = sql.Column(sql.Text(collation='utf8_general_ci'))
    property_type = sql.Column(sql.Text(collation='utf8_general_ci'))
    property_info = sql.Column(sql.Text(collation='utf8_general_ci'))
    class_name = sql.Column(sql.Text(collation='utf8_general_ci'))

    def toDict(self):
        return {'field_name'    :   self.property_name,
                'field_type'    :   self.property_type,
                'field_info'    :   self.property_info,
                'class_name'   :   self.class_name}

    def to_string(self):
        s = """
        :: ID: %d\n
        \t[+] Name: \t%s
        \t[+] Type: \t%s
        \t[+] Info: \t%s
        \t[+] Class: \t%s
        """ % (self.id, self.property_name, self.property_type,
               self.property_info, self.class_name)
        return textwrap.dedent(s)

    def __str__(self):
        return self.to_string()

    def __unicode__(self):
        return self.to_string()


class SmaliConstString(Base):
    """Models a Smali const string

    Attributes:
        id (integer): Primary key
        const_string_var (str): Name of the variable
        const_string_value (str): Value of const string

    """
    __tablename__ = "const_strings"

    # Fields
    id = sql.Column(sql.Integer, primary_key=True)
    const_string_var = sql.Column(sql.Text(collation='utf8_general_ci'))
    const_string_value = sql.Column(sql.Text(collation='utf8_general_ci'))
    class_name = sql.Column(sql.Text(collation='utf8_general_ci'))

    def toDict(self):
        return {'const_string_var'      :   self.const_string_var,
                'const_string_value'    :   self.const_string_value,
                'class_name'    :   self.class_name}

    def to_string(self):
        s = """
        :: ID: %d\n
        \t[+] Variable: \t%s
        \t[+] Value: \t%s
        \t[+] Class: \t%s
        """ % (self.id, self.const_string_var, self.const_string_value, self.class_name)

        return textwrap.dedent(s)

    def __str__(self):
        return self.to_string()

    def __unicode__(self):
        return self.to_string()


class SmaliMethod(Base):
    """Models a Smali class method

    Attributes:
        id (integer): Primary key
        method_name (str): Name of the method
        method_type (str): Method type (public, abstract, constructor)
        method_args (str): Method arguments (e.g. Landroid/os/Parcelable;Ljava/lang/ClassLoader;)
        method_ret (str): Methods return value (Z, I, [I, etc.)
        class_name (str): The class the method belongs to
    """
    __tablename__ = "methods"

    # Fields
    id = sql.Column(sql.Integer, primary_key=True)
    method_name = sql.Column(sql.Text(collation='utf8_general_ci'))
    method_type = sql.Column(sql.String(collation='utf8_general_ci', length=255))
    method_args = sql.Column(sql.Text(collation='utf8_general_ci'))
    method_ret = sql.Column(sql.Text(collation='utf8_general_ci'))
    class_name = sql.Column(sql.Text(collation='utf8_general_ci'))

    def toDict(self):
        return {'method_name'       :   self.method_name,
                'method_type'       :   self.method_type,
                'method_args'       :   self.method_args,
                'method_ret'        :   self.method_ret,
                'class_name'      :   self.method_ret}


    def to_string(self):
        s = """
        :: ID: %d\n
        \t[+] Name: \t%s
        \t[+] Type: \t%s
        \t[+] Args: \t%s
        \t[+] Ret: \t%s
        \t[+] Class: \t%s
        """ % (self.id, self.method_name, self.method_type,
               self.method_args, self.method_ret, self.class_name)
        return textwrap.dedent(s)

    def __str__(self):
        return self.to_string()

    def __unicode__(self):
        return self.to_string()


class SmaliCall(Base):
    """Models a Smali call (invoke-*)

    Attributes:
        id (integer): Primary key
        from_class (str): Name of calling class
        from_method (str): Name of calling method
        local_args (str): Local arguments
        dst_class (str): Called class
        dst_method (str): Called method
        dst_args (str): Called args
        ret (str): Return value

    """
    __tablename__ = "calls"

    # Fields
    id = sql.Column(sql.Integer, primary_key=True)

    # Source class/method/args
    from_class = sql.Column(sql.Text(collation='utf8_general_ci'))
    from_method = sql.Column(sql.Text(collation='utf8_general_ci'))
    local_args = sql.Column(sql.Text(collation='utf8_general_ci'))

    # Destination class/method/args
    dst_class = sql.Column(sql.Text(collation='utf8_general_ci'))
    dst_method = sql.Column(sql.Text(collation='utf8_general_ci'))
    dst_args = sql.Column(sql.Text(collation='utf8_general_ci'))

    # Return value
    ret = sql.Column(sql.Text(collation='utf8_general_ci'))

    def toDict(self):
        return {'from_class'    :   self.from_class,
                'from_method'   :   self.from_method,
                'local_args'    :   self.local_args,
                'dst_class'     :   self.dst_class,
                'dst_method'    :   self.dst_method,
                'dst_args'      :   self.dst_args,
                'ret'           :   self.ret}

    # FIXME: Add prettytable
    def to_string(self):
        s = """
        --------
        ID: \t%d

        From:
        \tClass: \t%s
        \tMethod: \t%s

        To:
        \tClass: \t%s
        \tMethod: \t%s

        Args:
        \tLocal: \t%s
        \tDest: \t%s
        --------
        """ % (self.id, self.from_class, self.from_method,
               self.dst_class, self.dst_method,
               self.local_args, self.dst_args)

        return s

    def __str__(self):
        return self.to_string()

    def __unicode__(self):
        return self.to_string()


class AppSQLModel:
    """Models an App as a SQL model

    This class modelates an application (:class:`smalisca.core.smalisca_app` as a SQL model.

    Attributes:
        db (session): A SQLAlchemy DB session
        classes (dict): Dict of classes
        properties (list): List of properties
        methods (list): List of methods
        calls (list): List of calls

    How to use:
        DATABASE='mysql://{0}:{1}@0.0.0.0:3306/{2}?charset=utf8mb4'.format(user, password, mysql_database_name)
        myDB = AppSQLModel(DATABASE)
        [...]
        myDB.add_classes(classes)
        myDB.add_properties(properties)
        [...]


    """

    @classmethod
    def connection(cls, raw_con, connection_record):
        if 'sqlite' in type(raw_con).__module__:
            raw_con.create_function('regexp', 2, regexp)


    def __init__(self, db):
        """Init the app SQL model

        Args:
            sqlitedb (str): SQLite file name

        Returns:
            AppSqlModel: Instance of AppSQLModel

        """
        #self.engine = sql.create_engine('sqlite:///' + sqlitedb)
        self.engine = sql.create_engine(db, encoding="utf-8", convert_unicode=False)
        event.listen(self.engine, 'connect', AppSQLModel.connection)

        Base.metadata.create_all(self.engine)

        # Create session
        self.session = scoped_session(sessionmaker(
            autoflush=True, autocommit=False,
            bind=self.engine
        ))
        self.db = self.session()

        # Internal instances
        self.classes = {}
        self.properties = []
        self.methods = []
        self.calls = []
        self.models_stack = []

    def get_class_by_name(self, classname):
        """Returns class obj specified by name

        Args:
            classname (str): Name of the class

        Returns
           class object

        """
        classes = self.db.query(SmaliClass)
        class_obj = classes.filter(SmaliClass.class_name == classname)

        # Check if any results:
        try:
            if self.db.query(class_obj.exists()):
                return class_obj.first()

        except sql.orm.exc.NoResultFound:
            log.warn("No result found")
            return None
        except sql.orm.exc.MultipleResultsFound:
            log.error("MultipleResultsFound:\n\tClass = {0}".format(classname))
            for q in class_obj.all():
                log.debug("\t+ {0}".format(q.class_name))
            raise sql.orm.exc.MultipleResultsFound('MultipleResultsFound')
        except:
            log.error("get_class_by_name failed")
            for q in class_obj.all():
                log.debug("\t+ {0}".format(q.class_name))
            raise

    def get_classes(self):
        """Returns all classes

        Returns:
            list: Return list of class objects

        """
        return self.db.query(SmaliClass).all()

    def get_properties(self):
        """Returns all properties

        Returns:
            list: Return list of property objects

        """
        return self.db.query(SmaliProperty).all()

    def get_const_strings(self):
        """Returns all const strings

        Returns:
            list: Return list of const-string objects

        """
        return self.db.query(SmaliConstString).all()

    def get_methods(self):
        """Return all methods

        Returns:
            list: Return list of method objects

        """
        return self.db.query(SmaliMethod).all()

    def get_calls(self):
        """Return all calls

        Returns:
            list: Return list of call objects

        """
        return self.db.query(SmaliCall).all()

    def save_all(self):
        self.db.add_all(self.models_stack)
        del self.models_stack[:]


    def add_classes(self, classes):
        self.engine.execute(SmaliClass.__table__.insert(),
                            classes)

    def add_class(self, class_obj, stack=False):
        """Add new class

        Args:
            class_obj (dict): Class object to insert

        """
        #log.debug(class_obj)
        new_class = SmaliClass(
            class_name=class_obj['name'],
            class_type=class_obj['type'],
            class_package=class_obj['package'],
            depth=class_obj['depth'],
            path=class_obj['path']
        )

        # Add new class
        self.classes[class_obj['name']] = new_class
        # self.db.merge(new_class, dont_load=True)
        if stack is False:
            self.db.add(new_class)
        else: self.models_stack.append(new_class)


    def add_properties(self, properties):
        self.engine.execute(SmaliProperty.__table__.insert(),
                            properties)

    def add_property(self, prop, stack=False):
        """Adds property to class

        Args:
            prop (dict): Property object to insert

        """
        class_obj = self.get_class_by_name(prop['class'])
        new_prop = SmaliProperty(
            property_name=prop['name'],
            property_type=prop['type'],
            property_info=prop['info'],
            class_name=prop['class']
        )

        # Append new property to class
        class_obj.properties.append(new_prop)

        # Add to DB
        try:
            # self.db.merge(class_obj, dont_load=True)
            if stack is False:
                self.db.add(class_obj)
            else: self.models_stack.append(class_obj)
        except sql.exc.IntegrityError:
            self.db.rollback()
            log.error("Insertion Failed: Found NOT unique values for property: {0}".format(new_prop))
            raise sql.exc.IntegrityError("Insertion Failed")


    def add_const_strings(self, const_strings):
        self.engine.execute(SmaliConstString.__table__.insert(),
                            const_strings)

    def add_const_string(self, const_string, stack=False):
        """Adds const string to class

        Args:
            prop (dict): Property object to insert

        """
        class_obj = self.get_class_by_name(const_string['class'])
        new_const_string = SmaliConstString(
            const_string_var=const_string['name'],
            const_string_value=const_string['value'],
            class_name=const_string['class']
        )

        # Append new const-string to class
        class_obj.const_strings.append(new_const_string)

        # Add to DB
        try:
            # self.db.merge(class_obj)
            if stack is False:
                self.db.add(class_obj)
            else: self.models_stack.append(class_obj)
        except:
            self.db.rollback()
            log.error("Insertion Failed: Failed inserting const-string\:%s" % new_const_string)
            raise

    def add_methods(self, methods):
        self.engine.execute(SmaliMethod.__table__.insert(),
                            methods)

    def add_method(self, method, stack=False):
        """Adds property to class

        Args:
            method (dict): Method object to insert

        """
        class_obj = self.get_class_by_name(method['class'])
        new_method = SmaliMethod(
            method_name=method['name'],
            method_type=method['type'],
            method_args=method['args'],
            method_ret=method['return'],
            class_name=method['class']
        )

        # Append new method to class
        class_obj.methods.append(new_method)

        # Add to DB
        try:
            # self.db.merge(class_obj)
            if stack is False:
                self.db.add(class_obj)
            else: self.models_stack.append(class_obj)

        except sql.exc.IntegrityError:
            self.db.rollback()
            log.error("Insertion Failed: Found NOT unique values for method: {0}".format(new_method))
            raise sql.exc.IntegrityError("Insertion Failed")

    def add_calls(self, calls):
        self.engine.execute(SmaliCall.__table__.insert(),
                            calls)

    def add_call(self, call, stack=False):
        """Adds calls to class

        Args:
            call (dict): Call object to insert

        """

        # Create new call object
        new_call = SmaliCall(
            # Origin
            from_class=call['from_class'],
            from_method=call['from_method'],
            local_args=call['local_args'],

            # Destination
            dst_class=call['to_class'],
            dst_method=call['to_method'],
            dst_args=call['dst_args'],

            # Return
            ret=call['return']
        )

        # Add new call to DB
        # self.db.merge(new_call)
        if stack is False:
            self.db.add(new_call)
        else: self.models_stack.append(new_call)

    def get_session(self):
        """Returns DB session

        Returns:

            Session: Returns DB session

        """
        return self.db

    def commit(self):
        """Commit changes/transactions"""
        self.db.commit()
