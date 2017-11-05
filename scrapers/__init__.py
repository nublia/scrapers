"""Web scapers.

This module implements a collection of web scrapers for data science
related projects.

fipe :
    Reads the market prices for vehicles sold in Brazil as published by
    Fipe -- Fundação Instituto de Pesquisas Econômicas.


Disclaimer
----------

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Copyright (C) 2017 Sebastian Krieger.

"""

from .fipe import Fipe

__author__ = 'Sebastian Krieger'
__copyright__ = 'Copyright 2007 Sebastian Krieger'
__credits__ = ['Sebastian Krieger']
__license__ = 'GNU GPL'
__version__ = '0.1.0'
__maintainer__ = 'Sebastian Krieger'
__email__ = 'sebastian@nublia.com'
__status__ = 'Development'

__all__ = ['Fipe']
