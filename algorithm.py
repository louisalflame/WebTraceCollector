#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, json, codecs, logging
from abc import ABCMeta, abstractmethod
from dom_analyzer import DomAnalyzer

class AlgoCrawler:
    __metaclass__ = ABCMeta

    @abstractmethod
    def set_utility(self, crawler, configuration, executor):
        pass

    @abstractmethod
    def prepare(self):
        pass

    @abstractmethod
    def add_new_events(self, state, prev_state, depth):
        pass  
        
    @abstractmethod
    def get_next_action(self, action_events):
        pass  

    @abstractmethod
    def trigger_action(self, state, new_edge, action, depth):
        pass  

    @abstractmethod
    def update_with_same_state(self, current_state, new_edge, action, depth, dom_list, url):
        pass  

    @abstractmethod
    def update_with_out_of_domain(self, current_state, new_edge, action, depth, dom_list, url):
        pass  

    @abstractmethod
    def update_with_new_state(self, current_state, new_state, new_edge, action, depth, dom_list, url):
        pass  

    @abstractmethod
    def update_with_old_state(self, current_state, new_state, new_edge, action, depth, dom_list, url):
        pass  

class DFScrawler(AlgoCrawler):
    def __init__(self):
        pass

    def set_utility(self, crawler, configuration, executor, automata):
        self.crawler = crawler
        self.configuration = configuration
        self.executor = executor
        self.automata = automata

    def prepare(self):
        #executor
        self.executor.start()
        self.executor.goto_url()

        #initial state
        initial_state = self.crawler.get_initail_state()
        self.crawler.run_script_before_crawl(initial_state)

    def add_new_events(self, state, prev_state, depth):
        for clickables, iframe_key in DomAnalyzer.get_clickables(state, prev_state if prev_state else None):
            for clickable in clickables:
                self.crawler.action_events.append( {
                        'state'  : state,
                        'action' : { 'clickable':clickable, 'iframe_key':iframe_key },
                        'depth'  : depth,
                    } )

    def get_next_action(self, action_events):
        event = action_events.pop()
        return event

    def trigger_action(self, state, new_edge, action, depth):
        logging.info(' |depth:%s state:%s| fire element in iframe(%s)', depth, state.get_id(), action['iframe_key'])
        self.crawler.make_value(new_edge)
        self.crawler.click_event_by_edge(new_edge)        

    def update_with_same_state(self, current_state, new_edge, action, depth, dom_list, url):
        # Do Nothing when same state
        return None

    def update_with_out_of_domain(self, current_state, new_edge, action, depth, dom_list, url):
        # back if state out of domain
        logging.info(' |depth:%s state:%s| out of domain: %s', depth, current_state.get_id(), url)
        logging.info('==========< BACKTRACK START >==========')
        logging.info('==<BACKTRACK> depth %s -> backtrack to state %s',depth ,current_state.get_id() )
        self.crawler.backtrack(current_state)
        logging.info('==========< BACKTRACK END   >==========')

    def update_with_new_state(self, current_state, new_state, new_edge, action, depth, dom_list, url):
        logging.info(' |depth:%s state:%s| add new state %s of : %s', depth, current_state.get_id(), new_state.get_id(), url )

        self.automata.save_state(new_state, depth)
        self.automata.save_state_shot(self.executor, new_state)

        if depth < self.configuration.get_max_depth():
            self.crawler.add_new_events(new_state, current_state, depth)

    def update_with_old_state(self, current_state, new_state, new_edge, action, depth, dom_list, url):
        #check if old state have a shorter depth
        if depth < new_state.get_depth():
            new_state.set_depth(depth)
            self.crawler.add_new_events(new_state, current_state, depth)


class MonkeyCrawler(AlgoCrawler):
    def __init__(self):
        pass

    def set_utility(self, crawler, configuration, executor):
        pass

    def prepare(self):
        pass

    def add_new_events(self, state, prev_state, depth):
        pass  
        
    def get_next_action(self, action_events):
        pass  

    def trigger_action(self, state, new_edge, action, depth):
        pass  

    def update_with_same_state(self, current_state, new_edge, action, depth, dom_list, url):
        pass  

    def update_with_out_of_domain(self, current_state, new_edge, action, depth, dom_list, url):
        pass  

    def update_with_new_state(self, current_state, new_state, new_edge, action, depth, dom_list, url):
        pass  

    def update_with_old_state(self, current_state, new_state, new_edge, action, depth, dom_list, url):
        pass  