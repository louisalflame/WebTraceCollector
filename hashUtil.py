#!/usr/bin/python
# -*- coding: utf-8 -*-

from dom_analyzer import DomAnalyzer

class Hash :
    def __init__(self, number, automata, configuration):
        self.number = number
        self.automata = automata
        self.configuration = configuration
        self.d = {}
        for j in range(number):
            x = []
            self.d[j] = x 
    
    def put(self, state):
        new_dom = state.get_all_normalize_dom(self.configuration)
        hashvalue = self.hash_function(new_dom)
        for list_id  in self.d[hashvalue]:
            list_dom = self.get_doms_by_stateID(list_id)
            if self.is_normalize_equal(list_dom, new_dom):
                return False, list_id
        list.append(self.d[hashvalue], state.get_id())
        return True, state.get_id()

    def hash_function(self, dom):
        return hash( dom ) % self.number

    def get_doms_by_stateID(self, stateID):
        return self.automata.get_state_by_id(stateID).get_all_normalize_dom(self.configuration)

    def is_normalize_equal(self, list_dom, new_dom):
        return DomAnalyzer.is_normalize_equal(list_dom, new_dom)