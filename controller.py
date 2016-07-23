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
    #config = SeleniumConfiguration(Browser.FireFox, "http://140.112.42.145:2000/demo/nothing/main.html")
    '''
            編號 & 網站名稱 & 網站類型 & URL \\ \hline
            1 & Facebook & Community platform & https://www.facebook.com/ \\ \hline
            2 & YouTube & Entertainment & https://www.youtube.com/ \\ \hline                  !! complex iframe  
            3 & Yahoo & Search engine & https://tw.yahoo.com/ \\ \hline                       !! too many Ineffective clickable 
            4 &　Google & Search engine & https://www.google.com.tw/ \\ \hline
            5 &　中時電子報 & News & http://www.chinatimes.com/ \\ \hline
            6 &　露天拍賣 & Commerce & http://www.ruten.com.tw/ \\ \hline
            7 &　聯合新聞網 & News & http://udn.com/news/index \\ \hline                      !! DIV 插入 BODY => DOM全錯 
            8 &　巴哈姆特 & Forum & http://www.gamer.com.tw/ \\ \hline                           always new sub domain 
            9 &　Mobile01 & Forum & http://www.mobile01.com/ \\ \hline
            10 & 蘋果日報　& News & http://www.appledaily.com.tw/ \\ \hline
            11 &　百度 & Search engine & https://www.baidu.com/ \\ \hline                     !! DIV BalloonSpacerLayer => 結構不對 DOM全錯 
            12 &　東森新聞雲 & News & http://www.ettoday.net/ \\ \hline                          always new window
            13 &　卡提諾論壇 & Forum & http://ck101.com/ \\ \hline
            14 &　伊莉討論區 & Forum & http://www40.eyny.com/index.php \\ \hline
            15 &　Hinet & Search engine & http://www.hinet.net/ \\ \hline                        always new window
            16 & 微軟Live.com　& Search engine & https://login.live.com/ \\ \hline 
            17 &　痞客邦 & Blog & https://www.pixnet.net/ \\ \hline                           !! DIV  => DOM全錯 
            18 &　PChome Online & Search engine & http://shopping.pchome.com.tw \\ \hline        always new sub domain
            19 & 淘寶　& Commerce & https://world.taobao.com/ \\ \hline                       !! too many Ineffective clickable 
            20 & Life生活網　& Blog & http://www.life.com.tw/ \\ \hline                          always new sub domain 
            21 & 104人力銀行 & Survice & http://104.com.tw/ \\ \hline                         !! too many Ineffective clickable 
            22 & 騰訊網 　& Search Engine & http://www.qq.com/ \\ \hline                         always new window
            23 & 新浪微博　& Community platform & http://www.weibo.com/login.php \\ \hline    !! DIV js_style_css_module_global_WB_outframe => 結構不對 DOM全錯 
            24 & 自由時報電子報　& News & http://www.ltn.com.tw/ \\ \hline                       new sub domain/ new window
            25 & 維基百科　& Dictionary & https://www.wikipedia.org/ \\ \hline                   new sub domain
            26 & 博客來　& Commerce & http://www.books.com.tw/ \\ \hline
            27 & 今日新聞網　& News & http://www.nownews.com/ \\ \hline                          always new window
            28 & 商業周刊　& News & http://www.businessweekly.com.tw/ \\ \hline                  always new window
            29 & 隨意窩Xuite　& Blog & http://xuite.net/ \\ \hline                               new sub domain/ new window
            30 & 1111人力銀行　& Survice & http://www.1111.com.tw/ \\ \hline
            31 & Flickr　& Community platform & https://www.flickr.com/ \\ \hline
            32 & Blogger　& Blog & http://www.blogger.com/ \\ \hline
            33 & 批踢踢實業坊　& Community platform & https://www.ptt.cc/index.html \\ \hline
            34 & FC2　& Survice & http://fc2.com/ \\ \hline
            35 & 卡卡洛普　& Survice & http://www.gamme.com.tw/ \\ \hline
            36 & PChome商店街　& Commerce & http://www.pcstore.com.tw/ \\ \hline
            37 & Giga Circle　& Survice & http://tw.gigacircle.com/ \\ \hline
            38 & 鉅亨網　& News & http://www.cnyes.com/ \\ \hline
            39 & momo購物網　& Commerce & http://www.momoshop.com.tw/main/Main.jsp \\ \hline
            40 & 蕃薯藤　& Search engine & http://www.yam.com/ \\ \hline
            41 & OB嚴選　& Commerce & http://www.obdesign.com.tw/ \\ \hline
            42 & GOMAJI　& Commerce & http://www.gomaji.com/Taipei \\ \hline
            43 & 愛評網　& Survice & http://www.ipeen.com.tw/ \\ \hline
            44 & 123KUBO酷播　& Entertainment & http://www.123kubo.com/ \\ \hline
            45 & 591租屋網　& Commerce & https://www.591.com.tw/ \\ \hline
            46 & TEEPR趣味新聞　& News & http://www.teepr.com/ \\ \hline
            47 & KKBOX　& Entertainment & https://www.kkbox.com/tw/tc/index.html \\ \hline
            48 & msn台灣　& Search Engine & http://www.msn.com/zh-tw/ \\ \hline
            49 & 微軟 & Survice & https://www.microsoft.com/zh-tw/ \\ \hline
            50 & T客邦　& Blog & http://www.techbang.com/ \\ \hline
    '''
    config = SeleniumConfiguration(Browser.FireFox, r"http://www.1111.com.tw/")
    print (config.get_url())
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
        else:
            make_dir(sys.argv[2], sys.argv[3])
            debugTestMain(sys.argv[2], sys.argv[3])
    else:
        print ("[WARNIING] needed argv: <Mode=0> <FolderPath> <Dirname> debug mode ")
        print ("[WARNIING] needed argv: <Mode=1> <WebSubmitID> <FolderPath> <Dirname> default crawling ")
        print ("                        <Mode=2> <FolderPath> <Dirname> <ConfigFile> <TracesFile>")
        print ("                                 <TraceID> <MutationMethodID> <MaxTraces> mutant crawling ")