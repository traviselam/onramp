"""Functionality to support interacting with an OnRamp Database

"""

import os
import json

class Database():

    def __init__(self, logger, auth):
        self._auth = auth
        self._logger = logger

    def is_connected(self):
        raise NotImplemented("Please implement this method")

    def connect(self):
        raise NotImplemented("Please implement this method")

    def disconnect(self):
        raise NotImplemented("Please implement this method")


    ##########################################################
    def is_valid_session_id(self, session_id):
        raise NotImplemented("Please implement this method")

    def is_valid_user_id(self, user_id):
        raise NotImplemented("Please implement this method")

    def is_valid_workspace_id(self, workspace_id):
        raise NotImplemented("Please implement this method")

    def is_valid_pce_id(self, pce_id):
        raise NotImplemented("Please implement this method")

    def is_valid_module_id(self, module_id):
        raise NotImplemented("Please implement this method")


    ##########################################################
    def is_active_session_id(self, session_id, user_id=None):
        raise NotImplemented("Please implement this method")

    def session_start(self, user_id):
        raise NotImplemented("Please implement this method")

    def session_update(self, session_id):
        raise NotImplemented("Please implement this method")

    def session_stop(self, session_id):
        raise NotImplemented("Please implement this method")

    ##########################################################
    def get_user_id(self, req_admin, username, password=None):
        raise NotImplemented("Please implement this method")

    def add_user(self, username, password):
        raise NotImplemented("Please implement this method")

    ##########################################################
    def get_workspace_id(self, name):
        raise NotImplemented("Please implement this method")

    def add_workspace(self, name):
        raise NotImplemented("Please implement this method")

    def lookup_user_in_workspace(self, workspace_id, user_id):
        raise NotImplemented("Please implement this method")

    def add_user_to_workspace(self, workspace_id, user_id):
        raise NotImplemented("Please implement this method")

    def lookup_pair_in_workspace(self, workspace_id, pm_pair_id):
        raise NotImplemented("Please implement this method")

    def add_pair_to_workspace(self, workspace_id, pm_pair_id):
        raise NotImplemented("Please implement this method")

    ##########################################################
    def get_pce_id(self, name):
        raise NotImplemented("Please implement this method")

    def add_pce(self, name):
        raise NotImplemented("Please implement this method")

    def lookup_module_in_pce(self, pce_id, module_id):
        raise NotImplemented("Please implement this method")

    def add_module_to_pce(self, pce_id, module_id):
        raise NotImplemented("Please implement this method")

    ##########################################################
    def get_module_id(self, name):
        raise NotImplemented("Please implement this method")

    def add_module(self, name):
        raise NotImplemented("Please implement this method")

    ##########################################################

    

from webapp.onrampdb_sqlite import Database_sqlite

##########################################
_current_db = None
_logger = None
_known_db = { 'sqlite' : Database_sqlite }

##########################################
def define_database( logger, dbtype, auth ):
    global _current_db
    global _known_db
    global _logger

    _logger = logger
    if dbtype not in _known_db:
        _logger.critical( "Database: \"%s\" is not supported." % (dbtype) )
        return -1

    if _current_db is None:
        _current_db = _known_db[dbtype](logger, auth)

    return 0


##########################################
# Valid keys
##########################################
def is_valid_user_id(user_id):
    db = _current_db
    db.connect()
    result = db.is_valid_user_id(user_id)
    db.disconnect()
    return result

def is_valid_workspace_id(workspace_id):
    db = _current_db
    db.connect()
    result = db.is_valid_workspace_id(workspace_id)
    db.disconnect()
    return result

def is_valid_pce_id(pce_id):
    db = _current_db
    db.connect()
    result = db.is_valid_pce_id(pce_id)
    db.disconnect()
    return result

def is_valid_module_id(module_id):
    db = _current_db
    db.connect()
    result = db.is_valid_module_id(module_id)
    db.disconnect()
    return result

def is_valid_job_id(module_id):
    return True

##########################################
# User Management
##########################################
def user_login(username, password):
    db = _current_db
    db.connect()
    user_id = db.get_user_id(False, username, password)
    session_id = db.session_start(user_id)
    db.disconnect()
    # TODO create a real apikey tied to this session
    return {'user_id': user_id, 'session_id': session_id, 'apikey' : session_id}

def user_update( auth ):
    db = _current_db
    db.connect()
    db.session_update( auth['session_id'] )
    db.disconnect()
    return True

def user_logout( auth ):
    db = _current_db
    db.connect()
    db.session_stop( auth['session_id'] )
    db.disconnect()
    return True

def check_user_apikey( apikey ):
    global _logger

    db = _current_db
    db.connect()
    result = db.is_active_session_id( apikey )
    db.disconnect()

    return result

def check_user_auth( auth, req_admin=False ):
    global _logger

    req_keys = ["session_id", "username", "user_id"]
    for key in req_keys:
        if key not in auth.keys():
            return False

    _logger.debug("DEBUG: " + str(req_admin))
    user_id = user_lookup( auth['username'], req_admin=req_admin )
    # Username does not exist
    if user_id is None:
        return False
    # ID mismatch
    elif user_id != auth['user_id']:
        return False
    # Session inactive -- TODO
    else:
        db = _current_db
        db.connect()
        result = db.is_active_session_id(auth['session_id'], auth['user_id'])
        db.disconnect()
        return result

    return True

##########################################
def user_add_if_new(username, password):
    db = _current_db
    db.connect()

    info = {}

    user_id = db.get_user_id(False, username)
    if user_id is not None:
        info['exists'] = True
    else:
        info['exists'] = False
        user_id = db.add_user(username, password)
    info['id'] = user_id

    db.disconnect()
    return info

##########################################
def user_lookup(username, req_admin=False):
    db = _current_db
    db.connect()
    user_id = db.get_user_id(req_admin, username)
    db.disconnect()
    return user_id

##########################################
def user_add(username, password):
    db = _current_db
    db.connect()
    user_id = db.add_user(username, password)
    db.disconnect()
    return user_id


##########################################
# Workspace Management
##########################################
def workspace_add_if_new(name):
    db = _current_db
    db.connect()

    info = {}

    workspace_id = db.get_workspace_id(name)
    if workspace_id is not None:
        info['exists'] = True
    else:
        info['exists'] = False
        workspace_id = db.add_workspace(name)
    info['id'] = workspace_id

    db.disconnect()
    return info

##########################################
def workspace_lookup(name):
    db = _current_db
    db.connect()
    work_id = db.get_workspace_id(name)
    db.disconnect()
    return work_id

##########################################
def workspace_add(name):
    db = _current_db
    db.connect()
    work_id = db.add_workspace(name)
    db.disconnect()
    return work_id

##########################################
def workspace_add_user(workspace_id, user_id):
    db = _current_db
    db.connect()

    info = {}

    if db.is_valid_workspace_id(workspace_id) is False:
        info['error_msg'] = "Invalid Workspace ID ("+workspace_id+")"
        db.disconnect()
        return info

    if db.is_valid_user_id(user_id) is False:
        info['error_msg'] = "Invalid User ID ("+user_id+")"
        db.disconnect()
        return info

    pair_id = db.lookup_user_in_workspace(workspace_id, user_id)
    if pair_id is not None:
        info['exists'] = True
    else:
        info['exists'] = False
        pair_id = db.add_user_to_workspace(workspace_id, user_id)
    info['id'] = pair_id

    db.disconnect()
    return info

##########################################
def workspace_add_pair(workspace_id, pce_id, module_id):
    db = _current_db
    db.connect()

    info = {}

    if db.is_valid_workspace_id(workspace_id) is False:
        info['error_msg'] = "Invalid Workspace ID ("+workspace_id+")"
        db.disconnect()
        return info

    if db.is_valid_pce_id(pce_id) is False:
        info['error_msg'] = "Invalid PCE ID ("+pce_id+")"
        db.disconnect()
        return info

    if db.is_valid_module_id(module_id) is False:
        info['error_msg'] = "Invalid Module ID ("+module_id+")"
        db.disconnect()
        return info

    pm_pair_id = db.lookup_module_in_pce(pce_id, module_id)
    if pm_pair_id is None:
        info['error_msg'] = "Invalid Module / PCE Pair (module="+module_id+", pce="+pce_id+")"
        db.disconnect()
        return info

    pair_id = db.lookup_pair_in_workspace(workspace_id, pm_pair_id)
    if pair_id is not None:
        info['exists'] = True
    else:
        info['exists'] = False
        pair_id = db.add_pair_to_workspace(workspace_id, pm_pair_id)
    info['id'] = pair_id

    db.disconnect()
    return info


##########################################
# PCE Management
##########################################
def pce_add_if_new(name):
    db = _current_db
    db.connect()

    info = {}

    pce_id = db.get_pce_id(name)
    if pce_id is not None:
        info['exists'] = True
    else:
        info['exists'] = False
        pce_id = db.add_pce(name)
    info['id'] = pce_id

    db.disconnect()
    return info

##########################################
def pce_lookup(name):
    db = _current_db
    db.connect()
    pce_id = db.get_pce_id(name)
    db.disconnect()
    return pce_id

##########################################
def pce_add(name):
    db = _current_db
    db.connect()
    pce_id = db.add_pce(name)
    db.disconnect()
    return pce_id

##########################################
def pce_add_module( pce_id, module_id ):
    db = _current_db
    db.connect()

    info = {}

    if db.is_valid_pce_id(pce_id) is False:
        info['error_msg'] = "Invalid PCE ID ("+pce_id+")"
        db.disconnect()
        return info

    if db.is_valid_module_id(module_id) is False:
        info['error_msg'] = "Invalid Module ID ("+module_id+")"
        db.disconnect()
        return info

    pair_id = db.lookup_module_in_pce(pce_id, module_id)
    if pair_id is not None:
        info['exists'] = True
    else:
        info['exists'] = False
        pair_id = db.add_module_to_pce(pce_id, module_id)
    info['id'] = pair_id

    db.disconnect()
    return info


##########################################
# Module Management
##########################################
def module_add_if_new(name):
    db = _current_db
    db.connect()

    info = {}

    module_id = db.get_module_id(name)
    if module_id is not None:
        info['exists'] = True
    else:
        info['exists'] = False
        module_id = db.add_module(name)
    info['id'] = module_id

    db.disconnect()
    return info

##########################################
def module_lookup(name):
    db = _current_db
    db.connect()
    module_id = db.get_module_id(name)
    db.disconnect()
    return module_id

##########################################
def module_add(name):
    db = _current_db
    db.connect()
    module_id = db.add_module(name)
    db.disconnect()
    return module_id
