"""This module test the Fipe scraper class.

"""
import unittest

from unittest import mock

from scrapers import fipe


# The method bellow will be used by the mock to replace requests.post
def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == ('http://veiculos.fipe.org.br/api/veiculos/'
                   'ConsultarTabelaDeReferencia'):
        return MockResponse([{'Codigo': 218, 'Mes': 'outubro/2017 '}], 200)
    elif args[0] == ('http://veiculos.fipe.org.br/api/veiculos/'
                     'ConsultarMarcas'):
        return MockResponse([{'Label': 'Acura', 'Value': '1'}], 200)
    elif args[0] == ('http://veiculos.fipe.org.br/api/veiculos/'
                     'ConsultarModelos'):
        return MockResponse({'Modelos': [{'Label': '19 16S/ RT 16V',
                                          'Value': 1986}],
                             'Anos': [{'Label': '32000 Gasolina',
                                       'Value': '32000-1'}]}, 200)
    elif args[0] == ('http://veiculos.fipe.org.br/api/veiculos/'
                     'ConsultarAnoModelo'):
        return MockResponse([{'Label': '2008 Gasolina', 'Value': '2008-1'}],
                            200)
    elif args[0] == ('http://veiculos.fipe.org.br/api/veiculos/'
                     'ConsultarValorComTodosParametros'):
        return MockResponse({'Valor': 'R$ 22.923,00', 'Marca': 'Renault',
                             'Modelo': 'Kangoo SPORTWAY 1.6/1.6 Hi-Flex',
                             'AnoModelo': 2008, 'Combustivel': 'Gasolina',
                             'CodigoFipe': '025128-3',
                             'MesReferencia': 'agosto de 2017 ',
                             'Autenticacao': 'lz260rgfdy5h', 'TipoVeiculo': 1,
                             'SiglaCombustivel': 'G',
                             'DataConsulta': '1 de agosto de 2017 16:44'}, 200)
    else:
        return MockResponse(None, 404)


class TestVariables(unittest.TestCase):
    def setUp(self):
        """Sets-up the test environment."""
        self.table = fipe.Table()
        self.car_maker = fipe.CarMaker(0, None, self.table)
        self.car_model = fipe.CarModel(0, None, self.car_maker)

    def test_table(self):
        self.assertEqual(self.table.id, 218)
        self.assertEqual(self.table.year, 2017)
        self.assertEqual(self.table.month, 10)

    def test_table_string(self):
        self.assertEqual(str(self.table), '218: outubro/2017')

    def test_car_maker(self):
        self.assertEqual(self.car_maker.id, 0)
        self.assertEqual(self.car_maker.name, None)
        self.assertEqual(self.car_maker.table.id, 218)
        self.assertEqual(self.car_maker.table.year, 2017)
        self.assertEqual(self.car_maker.table.month, 10)
        self.assertEqual(self.car_maker.vehicle_type, 1)

    def test_car_model(self):
        self.assertEqual(self.car_model.id, 0)
        self.assertEqual(self.car_model.name, None)
        self.assertEqual(self.car_model.maker.id, 0)
        self.assertEqual(self.car_model.maker.name, None)
        self.assertEqual(self.car_model.maker.table.id, 218)
        self.assertEqual(self.car_model.maker.table.year, 2017)
        self.assertEqual(self.car_model.maker.table.month, 10)
        self.assertEqual(self.car_model.maker.vehicle_type, 1)
        self.assertEqual(self.car_model.prices, [])

    def tearDown(self):
        """Shuts down the test environment."""
        pass


class TestFipe(unittest.TestCase):
    def setUp(self):
        """Sets-up the test environment."""
        self.fipe = fipe.Fipe()
        self.expected_table = fipe.Table(id=218, year=2017,
                                                  month='outubro')
        self.expected_car_maker = fipe.CarMaker(
            id=1, name='Acura', table=self.expected_table, vehicle_type=1)
        self.expected_car_model = fipe.CarModel(
            id=1986, name='19 16S/ RT 16V', maker=self.expected_car_maker)
        self.expected_price = fipe.CarPrice(2008, 1, price=22923.0,
                                                     fipe_code='025128-3')

    # We patch 'requests.post' with our own method. The mock object is passed
    # in to our test case method.
    @mock.patch('scrapers.fipe.requests.post',
                side_effect=mocked_requests_post)
    def test_crawl_reference_tables(self, mock_post):
        """Loads remote list of reference tables."""
        tables = self.fipe.crawl_reference_tables()
        self.assertIsInstance(tables, list)
        self.assertEqual(len(tables), 1)
        self.assertIsInstance(tables[0], fipe.Table)
        self.assertEqual(tables[0].id, self.expected_table.id)
        self.assertEqual(tables[0].year, self.expected_table.year)
        self.assertEqual(tables[0].month, self.expected_table.month)

    @mock.patch('scrapers.fipe.requests.post',
                side_effect=mocked_requests_post)
    def test_crawl_makers(self, mock_post):
        """Loads list of car makers."""
        makers = self.fipe.crawl_makers(table=self.expected_table)
        self.assertIsInstance(makers, list)
        self.assertEqual(len(makers), 1)
        self.assertIsInstance(makers[0], fipe.CarMaker)
        self.assertEqual(makers[0].id, self.expected_car_maker.id)
        self.assertEqual(makers[0].name, self.expected_car_maker.name)
        self.assertEqual(makers[0].table.id, self.expected_car_maker.table.id)
        self.assertEqual(makers[0].table.year,
                         self.expected_car_maker.table.year)
        self.assertEqual(makers[0].table.month,
                         self.expected_car_maker.table.month)
        self.assertEqual(makers[0].vehicle_type,
                         self.expected_car_maker.vehicle_type)

    @mock.patch('scrapers.fipe.requests.post',
                side_effect=mocked_requests_post)
    def test_crawl_models(self, mock_post):
        """Loads list of car models."""
        models = self.fipe.crawl_models(self.expected_car_maker)
        self.assertIsInstance(models, list)
        self.assertEqual(len(models), 1)
        self.assertIsInstance(models[0], fipe.CarModel)
        self.assertEqual(models[0].id, self.expected_car_model.id)
        self.assertEqual(models[0].name, self.expected_car_model.name)

    @mock.patch('scrapers.fipe.requests.post',
                side_effect=mocked_requests_post)
    def test_crawl_model_year(self, mock_post):
        """Loads list of make year by car models."""
        self.fipe.crawl_model_year(self.expected_car_model)
        self.assertIsInstance(self.expected_car_model.prices, list)
        self.assertEqual(len(self.expected_car_model.prices), 1)
        self.assertIsInstance(self.expected_car_model.prices[0],
                              fipe.CarPrice)
        self.assertEqual(self.expected_car_model.prices[0].build_year,
                         self.expected_price.build_year)
        self.assertEqual(self.expected_car_model.prices[0].fuel_type,
                         self.expected_price.fuel_type)

    @mock.patch('scrapers.fipe.requests.post',
                side_effect=mocked_requests_post)
    def test_crawl_model_price(self, mock_post):
        """Loads list of car models."""
        self.fipe.crawl_model_year(self.expected_car_model)
        self.fipe.crawl_model_price(self.expected_car_model)
        self.assertIsInstance(self.expected_car_model.prices, list)
        self.assertEqual(len(self.expected_car_model.prices), 1)
        self.assertIsInstance(self.expected_car_model.prices[0],
                              fipe.CarPrice)
        self.assertEqual(self.expected_car_model.prices[0].build_year,
                         self.expected_price.build_year)
        self.assertEqual(self.expected_car_model.prices[0].fuel_type,
                         self.expected_price.fuel_type)
        self.assertEqual(self.expected_car_model.prices[0].price,
                         self.expected_price.price)
        self.assertEqual(self.expected_car_model.prices[0].fipe_code,
                         self.expected_price.fipe_code)

    def tearDown(self):
        """Shuts down the test environment."""
        pass


if __name__ == '__main__':
    unittest.main()
