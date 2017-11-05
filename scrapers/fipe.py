"""Fipe web scraper.

This module implements a scraper to read the market prices for vehicles
sold in Brazil as published by  Fipe -- Fundação Instituto de Pesquisas
Econômicas. Data is retrieved from Fipe's webpage and stored in a local
SQLite database.

"""
import requests
import sqlite3

from os.path import dirname
from time import sleep


class Table():
    """Fipe reference table object."""
    months = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
              'julho', 'agosto', 'setembro', 'outubro', 'novembro',
              'dezembro']

    def __init__(self, id=218, year=2017, month=10):
        self.id = id
        self.year = year
        if isinstance(month, int):
            self.month = month
        elif isinstance(month, str):
            self.month = self.months.index(month) + 1
        else:
            raise ValueError('Invalide month `{}`.'.format(month))

    def __str__(self):
        return '{}: {}/{}'.format(self.id, self.months[self.month-1],
                                  self.year)


class CarMaker():
    """Fipe car maker object."""

    def __init__(self, id, name, table, vehicle_type=1):
        self.id = id
        self.name = name
        if isinstance(table, Table):
            self.table = table
        else:
            raise TypeError('Invalid table `{}`.'.format(table))
        self.vehicle_type = vehicle_type


class CarModel():
    """Fipe car model object."""

    def __init__(self, id, name, maker):
        self.id = id
        self.name = name
        self.maker = maker
        self.prices = []

    def add_price(self, year, fuel_type):
        """Add built year/price to car model."""
        self.prices.append(CarPrice(year, fuel_type))

    def update_price(self, i, **kwargs):
        """Update i-th price of car model."""
        for key, value in kwargs.items():
            setattr(self.prices[i], key, value)


class CarPrice():
    """Fipe car price by year and fuel type."""

    def __init__(self, build_year, fuel_type, price=None, fipe_code=None):
        self.build_year = build_year
        self.fuel_type = fuel_type
        self.price = price
        self.fipe_code = fipe_code


class Fipe():
    """Fipe web scraper.

    Class to collect vehicle marked prices in Brazil as published by
    Fipe -- Fundação Instituto de Pesquisas Econômicas.

    Examples
    --------
    >> fipe = Fipe()
    >> tables = fipe.crawl_reference_tables()
    >> car_makers = fipe.crawl_makers(table=tables[0])
    >> car_models = fipe.crawl_models(car_makers[0])
    >> fipe.crawl_model_year(car_models[0])
    >> fipe.crawl_model_year(car_models[0])

    """
    base_url = 'http://veiculos.fipe.org.br'

    def __init__(self):
        pass

    def crawl_reference_tables(self):
        """Returns a pandas.DataFrame of reference tables."""
        url = '{}/api/veiculos/ConsultarTabelaDeReferencia'.format(
            self.base_url)
        response = self._post_request(url)
        # Converts raw data into usefull variables.
        tables = []
        for item in response:
            _month, _year = item['Mes'].split('/')
            tables.append(Table(id=item['Codigo'], year=int(_year),
                                month=_month))
        # Finally, return the dataframe of reference tables.
        return tables

    def crawl_makers(self, table=Table(), vehicle_type=1):
        """Crawls FIPE car makers.

        Parameters
        ----------
        table : Table, optional
            Reference table.
        vehicle_type : integer, optional
            Type of vehicle (1=car).

        Returns
        -------
        lst : list
            List of car maker objects.

        """
        url = '{}/api/veiculos/ConsultarMarcas'.format(self.base_url)
        data = {'codigoTabelaReferencia': table.id,
                'codigoTipoVeiculo': vehicle_type}
        response = self._post_request(url, data=data)
        # Converts raw data.
        makers = []
        for item in response:
            makers.append(CarMaker(id=int(item['Value']), name=item['Label'],
                          table=table, vehicle_type=vehicle_type))
        # Finally, return the dataframe of car makers
        return makers

    def crawl_models(self, maker):
        """Returns a pandas.DataFrame of models by car maker.

        Parameters
        ----------
        maker : CarMaker
            Car maker object.

        Returns
        -------
        lst : list
            List of car model objects by maker.

        """
        assert isinstance(maker, CarMaker)
        #
        url = '{}/api/veiculos/ConsultarModelos'.format(self.base_url)
        data = {'codigoTipoVeiculo': maker.vehicle_type,
                'codigoTabelaReferencia': maker.table.id,
                # 'codigoModelo': None,
                'codigoMarca': maker.id,
                # 'ano': None,
                # 'codigoTipoCombustivel': None,
                # 'anoModelo': None
                # 'modeloCodigoExterno': None
                }
        response = self._post_request(url, data=data)
        # Converts raw data.
        models = []
        for item in response['Modelos']:
            models.append(CarModel(id=int(item['Value']), name=item['Label'],
                                   maker=maker))
        # Finally, return the dataframe of car makers
        return models

    def crawl_model_year(self, model):
        """Crawls and appends built year by car model.

        Parameters
        ----------
        model: CarModel
            Car model object.

        Returns
        -------
        Nothing.

        """
        assert isinstance(model, CarModel)
        url = '{}/api/veiculos/ConsultarAnoModelo'.format(self.base_url)
        data = {'codigoTipoVeiculo': model.maker.vehicle_type,
                'codigoTabelaReferencia': model.maker.table.id,
                'codigoModelo': model.id,
                'codigoMarca': model.maker.id,
                # 'ano': None
                # 'codigoTipoCombustivel': None
                # 'anoModelo': None
                # 'modeloCodigoExterno': None
                }
        response = self._post_request(url, data=data)
        # Converts raw data.
        # fuel_types = {'Gasolina': 1, 'Álcool': 2, 'Diesel': 3}
        for item in response:
            _year, _fuel_type = item['Value'].split('-')
            model.add_price(int(_year), int(_fuel_type))

    def crawl_model_price(self, model, irange=None):
        """Crawls and updates car model prices.

        Parameters
        ----------
        model : CarModel
            Car model object.
        irange: list or integer, optional
            Indices of built years/prices to crawl. If `None`, then
            crawls all available built years (default).

        Returns
        -------
        Nothing.

        """
        if irange is None:
            irange = range(len(model.prices))

        if model.maker.vehicle_type == 1:
            vehicle_type_descriptor = 'carro'
        else:
            raise ValueError('Invalid vehicle type: {}'.format(
                model.maker.vehicle_type))

        for i in irange:
            data = {'codigoTabelaReferencia': model.maker.table.id,
                    'codigoMarca': model.maker.id,
                    'codigoModelo': model.id,
                    'codigoTipoVeiculo': model.maker.vehicle_type,
                    'anoModelo': model.prices[i].build_year,
                    'codigoTipoCombustivel': model.prices[i].fuel_type,
                    'tipoVeiculo': vehicle_type_descriptor,
                    'modeloCodigoExterno': None,
                    'tipoConsulta': 'tradicional'
                    }
            url = '{}/api/veiculos/ConsultarValorComTodosParametros'.format(
                self.base_url)
            response = self._post_request(url, data=data)
            # Finally, return the dataframe of car makers
            price = ''
            for s in response['Valor']:
                if s in '1234567890':
                    price += s
                elif s == ',':
                    price += '.'
            #
            model.update_price(i, price=float(price),
                               fipe_code=response['CodigoFipe'])

    def _post_request(self, url, headers=None, data=None):
        """Makes post request and returns JSON data."""
        default_headers = {
            'Host': 'veiculos.fipe.org.br',
            # 'User-Agent': 'nublia.scraper/0.1',
            'User-Agent': ('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) '
                           'Gecko/20100101 Firefox/54.0'),
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': '{}/'.format(self.base_url),
            'DNT': '1',
            'Connection': 'keep-alive',
        }
        headers = headers or default_headers
        n = 5
        while True:
            try:
                response = requests.post(url, data=data, headers=headers)
                return response.json()
            except (requests.ConnectionError,
                    requests.exceptions.ChunkedEncodingError) as e:
                print('ConnectionError: I will try again in {:d} s.'
                      .format(n))
                sleep(n)
                n *= 2
                pass
            except requests.models.complexjson.JSONDecodeError:
                print('JSONDecodeError: I will try again in {:d} s.'
                      .format(n))
                sleep(n)
                n *= 2
                pass

        raise RuntimeError('I am not supposed to be here!')


class Fipe_db():
    """
    Fipe database.

    Class to manage vehicle marked prices in Brazil as published by
    Fipe -- Fundação Instituto de Pesquisas Econômicas.

    Parameters
    ----------
    db : string, optional
        Path of the SQLite database. The default is to store data in
        memory only. Remember to use absolute paths.

    Examples
    --------
    >> fipe = Fipe(':memory:')
    >> import os
    >> fipe = Fipe(os.path.realpath('../dat/dataset.db'))

    """
    module_dir = dirname(__file__)

    def __init__(self, db=':memory:'):
        self.connect(db)

    def connect(self, db):
        """Connects to SQLite database."""
        # Connects to database
        self.conn = sqlite3.connect(db, isolation_level='Exclusive')
        # Sets cursor
        self.cursor = self.conn.cursor()
        # Some optimization (https://stackoverflow.com/questions/
        # 16572399/python-sqlite-cache-in-memory)
        # self.cursor.execute('PRAGMA synchronous = 0;')
        # self.cursor.execute('PRAGMA journal_mode = OFF;')
        # self.conn.commit()

    def create_schema(self):
        """Creates Fipe database schema."""
        self._execute_script_from_file('{}/schemas/{}'.format(
            self.module_dir, 'fipe_db_model.sql'))

    def close(self):
        """Closes the database connection."""
        self.cursor.close()
        self.conn.close()

    def _execute_script_from_file(self, url):
        """Executes SQL script in file given by `url`."""
        with open(url, 'r') as f:
            self.cursor.executescript(''.join(f.readlines()))
            self.conn.commit()
