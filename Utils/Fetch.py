import gzip
import pickle

import psycopg2
import pymongo
from ParadoxTrading.Utils.DataStruct import DataStruct
from pymongo import MongoClient
from redis import StrictRedis


class Fetch:

    mongo_host = 'localhost'
    mongo_prod_db = 'FutureProd'
    mongo_inst_db = 'FutureInst'

    pgsql_host = 'localhost'
    pgsql_dbname = 'FutureData'
    pgsql_user = 'pang'
    pgsql_password = ''

    def productList() -> list:
        client = MongoClient(host=Fetch.mongo_host)
        db = client[Fetch.mongo_prod_db]
        ret = db.collection_names()
        client.close()

        return ret

    def productIsTrade(_product: str, _tradingday: str) -> bool:
        """
        check whether product is traded on tradingday

        Args:
            _product (str): which product.
            _tradingday (str): which day.

        Returns:
            bool: True for traded, False for not
        """
        client = MongoClient(host=Fetch.mongo_host)
        db = client[Fetch.mongo_prod_db]
        coll = db[_product]
        count = coll.count({'TradingDay': _tradingday})
        client.close()

        return count > 0

    def productLastTradingDay(_product: str, _tradingday: str) -> str:
        """
        get the first day less then _tradingday of _product

        Args:
            _product (str): which product.
            _tradingday (str): which day.

        Returns:
            str: if None, it means nothing found
        """
        client = MongoClient(host=Fetch.mongo_host)
        db = client[Fetch.mongo_prod_db]
        coll = db[_product]
        d = coll.find_one(
            {'TradingDay': {'$lt': _tradingday}},
            sort=[('TradingDay', pymongo.DESCENDING)]
        )
        client.close()

        return d['TradingDay'] if d is not None else None

    def productNextTradingDay(_product: str, _tradingday: str) -> str:
        """
        get the first day greater then _tradingday of _product

        Args:
            _product (str): which product.
            _tradingday (str): which day.

        Returns:
            str: if None, it means nothing found
        """
        client = MongoClient(host=Fetch.mongo_host)
        db = client[Fetch.mongo_prod_db]
        coll = db[_product]
        d = coll.find_one(
            {'TradingDay': {'$gt': _tradingday}},
            sort=[('TradingDay', pymongo.ASCENDING)]
        )
        client.close()

        return d['TradingDay'] if d is not None else None

    def fetchTradeInstrument(_product: str, _tradingday: str) -> list:
        """
        fetch all traded insts of one product on tradingday

        Args:
            _product (str): which product.
            _tradingday (str): which day.

        Returns:
            list: list of str. if len() == 0, then no traded inst
        """
        client = MongoClient(host=Fetch.mongo_host)
        db = client[Fetch.mongo_prod_db]
        coll = db[_product]
        data = coll.find_one({'TradingDay': _tradingday})
        ret = []
        if data is not None:
            ret = data['InstrumentList']
        client.close()

        return ret

    def fetchDominant(_product: str, _tradingday: str) -> str:
        """
        fetch dominant instrument of one product on tradingday

        Args:
            _product (str): which product.
            _tradingday (str): which day.

        Returns:
            str: dominant instrument. if None, then no traded inst
        """
        client = MongoClient(host=Fetch.mongo_host)
        db = client[Fetch.mongo_prod_db]
        coll = db[_product]
        data = coll.find_one({'TradingDay': _tradingday})
        ret = None
        if data is not None:
            ret = data['Dominant']
        client.close()

        return ret

    def fetchSubDominant(_product: str, _tradingday: str) -> str:
        """
        fetch sub dominant instrument of one product on tradingday

        Args:
            _product (str): which product.
            _tradingday (str): which day.

        Returns:
            str: sub dominant instrument. if None, then no traded inst
        """
        client = MongoClient(host=Fetch.mongo_host)
        db = client[Fetch.mongo_prod_db]
        coll = db[_product]
        data = coll.find_one({'TradingDay': _tradingday})
        ret = None
        if data is not None:
            ret = data['SubDominant']
        client.close()

        return ret

    def fetchIntraDayData(
            _product: str, _tradingday: str,
            _instrument: str=None, _sub_dominant: bool=False,
            _index: str='HappenTime') -> DataStruct:
        """
        fetch each tick data of product(dominant) or instrument from begin date to end date

        Args:
            _product (str): if None using _instrument, else using dominant inst of _product
            _tradingday (str):
            _instrument (str): if _product is None, then using _instrument
            _sub_dominant (bool): if True and _product is not None, using sub dominant of _product

        Returns:
            DataStruct:
        """
        # set inst to real instrument name
        inst = _instrument
        if _product is not None:
            if not _sub_dominant:
                inst = Fetch.fetchDominant(_product, _tradingday)
            else:
                inst = Fetch.fetchSubDominant(_product, _tradingday)

        # check instrument valid
        if inst is None:
            return None

        con = psycopg2.connect(
            dbname=Fetch.pgsql_dbname,
            host=Fetch.pgsql_host,
            user=Fetch.pgsql_user,
            password=Fetch.pgsql_password,
        )
        cur = con.cursor()

        # get all column names
        cur.execute(
            "select column_name from information_schema.columns " +
            "where table_name='" + inst + "'"
        )
        columns = []
        for d in cur.fetchall():
            columns.append(d[0])

        # get all ticks
        cur.execute(
            "SELECT * FROM " + inst +
            " WHERE TradingDay='" + _tradingday +
            "' ORDER BY HappenTime"
        )
        datas = list(cur.fetchall())
        con.close()

        # turn into datastruct
        datastruct = DataStruct(columns, _index.lower(), datas)

        return datastruct

if __name__ == '__main__':
    ret = Fetch.productList()
    assert type(ret) == list
    print('Fetch.productList', len(ret))

    ret = Fetch.productIsTrade('rb', '20170123')
    assert ret
    print('Fetch.productIsTrade', ret)

    ret = Fetch.productLastTradingDay('rb', '20170123')
    assert type(ret) == str
    print('Fetch.productLastTradingDay', ret)

    ret = Fetch.productNextTradingDay('rb', '20170123')
    assert type(ret) == str
    print('Fetch.productNextTradingDay', ret)

    ret = Fetch.fetchTradeInstrument('rb', '20170123')
    assert type(ret) == list
    print('Fetch.fetchTradeInstrument', len(ret))

    ret = Fetch.fetchDominant('rb', '20170123')
    assert type(ret) == str
    print('Fetch.fetchDominant', ret)

    ret = Fetch.fetchSubDominant('rb', '20170123')
    assert type(ret) == str
    print('Fetch.fetchSubDominant', ret)
