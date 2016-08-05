#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Module docstring
"""

import os, sys, json, posixpath, time, codecs, datetime, logging, traceback
from configuration import SeleniumConfiguration, Browser, MutationMethod
from automata import Automata, State
from algorithm import DFScrawler, MonkeyCrawler, CBTMonkeyCrawler
from clickable import Clickable, InputField, SelectField
from connecter import mysqlConnect, nullConnect
from crawler import SeleniumCrawler
from data_bank import MysqlDataBank, InlineDataBank
from dom_analyzer import DomAnalyzer
from executor import SeleniumExecutor
from normalizer import AttributeNormalizer, TagNormalizer, TagWithAttributeNormalizer
from visualizer import Visualizer

#==============================================================================================================================
# Selenium Web Driver
#==============================================================================================================================
def SeleniumMain(web_submit_id, folderpath=None, dirname=None):
    logging.info(" connect to mysql")
    databank = MysqlDataBank("localhost", "jeff", "zj4bj3jo37788", "test")
    url, deep, time = databank.get_websubmit(web_submit_id)

    logging.info(" setting config...")
    config = SeleniumConfiguration(Browser.PhantomJS, url, folderpath, dirname)
    config.set_max_depth(deep)
    config.set_max_time(int(time)*60)
    config.set_simple_clickable_tags()
    config.set_simple_inputs_tags()
    config.set_simple_normalizers()
    config.set_frame_tags(['iframe'])
    
    logging.info(" setting executor...")
    executor = SeleniumExecutor(config.get_browserID(), config.get_url())
    
    logging.info(" setting crawler...")
    automata = Automata()
    crawler = SeleniumCrawler(config, executor, automata, databank)
    
    logging.info(" crawler start run...")
    automata = crawler.run()
    crawler.close()
    
    logging.info(" end! save automata...")
    automata.save_automata(config)
    automata.save_traces(config)
    Visualizer.generate_html('web', os.path.join(config.get_path('root'), config.get_automata_fname()))
    config.save_config('config.json')

def SeleniumMutationTrace(folderpath, dirname, config_fname, traces_fname, trace_id, method_id, modes):
    logging.info(" loading config...")
    config = load_config(config_fname)
    config.set_folderpath(folderpath)
    config.set_dirname(dirname)
    config.set_mutation_trace(traces_fname, trace_id)
    config.set_mutation_method(method_id)
    config.set_mutation_modes(modes)

    logging.info(" setting executor...")
    executor = SeleniumExecutor(config.get_browserID(), config.get_url())

    logging.info(" setting crawler...")
    automata = Automata()
    databank = MysqlDataBank("localhost", "jeff", "zj4bj3jo37788", "test")
    crawler = SeleniumCrawler(config, executor, automata, databank)

    logging.info(" crawler start run...")
    crawler.run_mutant()

    logging.info(" end! save automata...")
    automata.save_traces(config)
    automata.save_automata(config)    
    Visualizer.generate_html('web', os.path.join(config.get_path('root'), config.get_automata_fname()))

def debugTestMain(folderpath, dirname):
    logging.info(" setting config...")
    config = SeleniumConfiguration(Browser.FireFox, r"http://www.1111.com.tw/")
    config.set_max_depth(5)
    config.set_max_length(4)
    config.set_trace_amount(2)
    config.set_max_states(100)
    config.set_folderpath(folderpath)
    config.set_dirname(dirname)
    #config.set_frame_tags(['iframe'])

    config.set_dom_inside_iframe(True)
    config.set_simple_clickable_tags()
    config.set_simple_inputs_tags()
    config.set_simple_normalizers()

    logging.info(" setting executor...")
    executor = SeleniumExecutor(config.get_browserID(), config.get_url())

    logging.info(" setting crawler...")
    automata = Automata(config)
    databank = MysqlDataBank("140.112.42.147", "jeff", "zj4bj3jo37788", "test")
    algorithm = MonkeyCrawler() 
    crawler = SeleniumCrawler(config, executor, automata, databank, algorithm)

    logging.info(" crawler start run...")
    crawler.run_algorithm()

    logging.info(" end! save automata...")
    algorithm.save_traces()
    automata.save_automata(config.get_automata_fname())
    Visualizer.generate_html('web', os.path.join(config.get_path('root'), config.get_automata_fname()))
    config.save_config('config.json')
#==============================================================================================================================

def load_automata(fname):
    t_start = time.time()
    assert os.path.isfile(fname) and os.path.exists(fname)
    automata = Automata()
    with open(fname) as f:
        data = json.load(f)
        for state in data['state']:
            with open(os.path.join(os.path.dirname(os.path.realpath(fname)), state['dom_path']), 'r') as df:
                s = State(df.read())
                s.set_id(state['id'])
                for clickable in state['clickable']:
                    c = Clickable(clickable['id'], clickable['xpath'], clickable['tag'])
                    s.add_clickable(c)
                automata.add_state(s)
        for edge in data['edge']:
            from_state = automata.get_state_by_id(edge['from'])
            to_state = automata.get_state_by_id(edge['to'])
            clickable = from_state.get_clickable_by_id(edge['clickable'])
            assert from_state and to_state and clickable
            automata.add_edge(from_state, to_state, clickable)
    return automata

def load_config(fname):
    t_start = time.time()
    with codecs.open(fname, encoding='utf-8') as f:
        data = json.load(f)
        browser = Browser.PhantomJS if data['browser_id'] == 3 \
            else Browser.Chrome if data['browser_id'] == 2 else Browser.FireFox
        config = SeleniumConfiguration(browser, data['url'], data['dirname'], data['folderpath'])
        config.set_max_depth(int(data['max_depth']))
        config.set_max_states(int(data['max_states']))
        config.set_sleep_time(int(data['sleep_time']))
        config.set_max_time(int(data['max_time']))
        # ignore the rest ('automata_fname', 'root_path', 'dom_path', 'state_path', 'clickable_path')
        config.set_automata_fname(data['automata_fname'])
        config.set_domains(data['domains'])
        config.set_dom_inside_iframe(data['dom_inside_iframe'])
        config.set_traces_fname(data['traces_fname'])

        if data['analyzer']['simple_clickable_tags']:
            config.set_simple_clickable_tags()
        if data['analyzer']['simple_normalizers']:
            config.set_simple_normalizers()
        if data['analyzer']['simple_inputs_tags']:
            config.set_simple_inputs_tags()
        for tag in data['analyzer']['clickable_tags']:
            config.set_clickable_tags(tag['tag'], tag['attr'], tag['value'])
        for tag in data['analyzer']['inputs_tags']:
            config.set_inputs_tags(tag)
        config.set_tags_normalizer(data['analyzer']['tag_normalizers'])
        config.set_attributes_normalizer(data['analyzer']['attributes_normalizer'])
        for tag in data['analyzer']['tag_with_attribute_normalizers']:
            config.set_tag_with_attribute_normalizer(tag['tag'], tag['attr'], tag['value'], tag['mode'])

        if data['before_trace_fname']:
            config.set_before_trace(data['before_trace_fname'])
    return config


def make_dir(folderpath=None, dirname=None):
    dirname = datetime.datetime.now().strftime('%Y%m%d%H%M%S') if not dirname else dirname
    root_path = os.path.join('trace', dirname ) if not folderpath else os.path.join( folderpath, dirname )
    file_path = {
        'root': root_path,
        'dom': os.path.join(root_path, 'dom'),
        'state': os.path.join(root_path, 'screenshot', 'state')
    }
    for key, value in file_path.items():
        abs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), value)
        if not os.path.exists(abs_path):
            os.makedirs(abs_path)
    make_log(folderpath, dirname)

def make_log(folderpath, dirname):
    filename = os.path.join( os.path.dirname(os.path.realpath(__file__)), os.path.join(folderpath, dirname, 'log.txt') )
    level = logging.INFO
    form = '[%(asctime)s]<%(levelname)s>: %(message)s'
    logging.basicConfig(filename=filename, level=level, format=form)

def end_log(filename, complete, note):
    with open(filename, 'w') as end_file:
        end = {
            'complete': complete,
            'note': note
        }
        json.dump(end, end_file, indent=2, sort_keys=True, ensure_ascii=False)

if __name__ == '__main__':
    if len(sys.argv)> 1:
        #default mode
        if  sys.argv[1] == '1':
            try:
                if not os.path.isdir(sys.argv[3]) or not os.path.exists(sys.argv[3]):
                    raise ValueError('not found folder')
                if os.path.exists( os.path.join(sys.argv[3], sys.argv[4]) ):
                    raise ValueError('dirname already exist')
                make_dir(sys.argv[3], sys.argv[4])
                try:
                    SeleniumMain(sys.argv[2], sys.argv[3], sys.argv[4])
                    end_log( os.path.join(sys.argv[3], sys.argv[4], 'end.json'), True, 'done')
                except Exception as e:
                    end_log( os.path.join(sys.argv[3], sys.argv[4], 'end.json'),False, traceback.format_exc())
            except Exception as e:  
                with open("default_log.txt","a") as main_log:
                    main_log.write( '\n[MAIN ERROR-%s]: %s' % (datetime.datetime.now().strftime('%Y%m%d%H%M%S'), traceback.format_exc()) )
        #mutant mode
        elif sys.argv[1] == '2':
            try:
                if os.path.exists( os.path.join(sys.argv[2], sys.argv[3]) ):
                    raise ValueError('dirname already exist')
                if not os.path.isfile(sys.argv[4]) or not os.path.exists(sys.argv[4]):
                    raise ValueError('not found config file')
                if not os.path.isfile(sys.argv[5]) or not os.path.exists(sys.argv[5]):
                    raise ValueError('not found traces file')
                make_dir(sys.argv[2], sys.argv[3])
                try:
                    SeleniumMutationTrace(sys.argv[2], sys.argv[3], sys.argv[4], 
                        sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8])
                    end_log( os.path.join(sys.argv[2], sys.argv[3], 'end.json'), True, 'done')
                except Exception as e:
                    end_log( os.path.join(sys.argv[2], sys.argv[3], 'end.json'),False, traceback.format_exc())
            except Exception as e:
                with open("mutant_log.txt","a") as main_log:
                    main_log.write( '[MAIN ERROR-%s]: %s' % (datetime.datetime.now().strftime('%Y%m%d%H%M%S'), traceback.format_exc()) )
        elif sys.argv[1] == '0':
            make_dir(sys.argv[2], sys.argv[3])
            debugTestMain(sys.argv[2], sys.argv[3])
    else:
        print ("[WARNIING] needed argv: <Mode=0> <FolderPath> <Dirname> debug mode ")
        print ("[WARNIING] needed argv: <Mode=1> <WebSubmitID> <FolderPath> <Dirname> default crawling ")
        print ("                        <Mode=2> <FolderPath> <Dirname> <ConfigFile> <TracesFile>")
        print ("                                 <TraceID> <MutationMethodID> <MaxTraces> mutant crawling ")