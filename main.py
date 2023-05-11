## Interactive Dashboard
## A hopefully idiot-proof self-service reporting tool for the technically illiterate
## Cache McClure
## Manager, Data Architecture and Engineering
## ReserveBar.com


## Import Modules
from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow
from pyqtgraph.dockarea import *
from sqlalchemy import create_engine
import pandas as pd
from pickle import load as pload
from pickle import dump as pdump
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta
from os.path import exists
import sys


## Classes
## Dock Area
class DockArea(DockArea):
    ## This is to prevent the Dock from being resized
    def makeContainer(self, typ):
        new = super(DockArea, self).makeContainer(typ)
        new.setChildrenCollapsible(False)
        return new


## Main Window
class mainWindow(QMainWindow):
    ## Initialize Class
    def __init__(self):
        super(mainWindow,self).__init__()
        self.initUI()
    

    ## Initialize User Interface
    def initUI(self):
        ## Initial Setup
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        ## Read Master SQL Query
        with open('master_query.sql') as f:
            self.sql = f.read()

        ## Dock Area
        dock_area = DockArea(self)

        ## Dock 1
        self.dock1 = Dock('Widget 1',size=(300,500))
        self.dock1.hideTitleBar()
        dock_area.addDock(self.dock1)

        ## Dock 2
        self.dock2 = Dock('Widget 2',size=(400,500))
        self.dock2.hideTitleBar()
        dock_area.addDock(self.dock2,'right',self.dock1)

        ## Add Widgets
        self.widget_one = FilterWidget(self)
        self.widget_two = PlotlyWidget(self)

        ## Buttons
        ## Exit Button
        self.exit_b = QtWidgets.QPushButton(self)
        self.exit_b.setText('Exit')
        self.exit_b.clicked.connect(self.close)

        ## Plot Button
        self.plot_b = QtWidgets.QPushButton(self)
        self.plot_b.setText('Plot')
        self.plot_b.clicked.connect(self.showPlot)

        ## Retrieve Data Button
        self.ret_b = QtWidgets.QPushButton(self)
        self.ret_b.setText('Retrieve Data')
        self.ret_b.clicked.connect(self.retData)
        self.ret_label = QtWidgets.QLabel(self)
        self.ret_label.setText('No Data')
        self.ret_label.setFixedHeight(30)
        self.ret_label.setAlignment(QtCore.Qt.AlignCenter)

        ## Export to CSV Button
        self.export_b = QtWidgets.QPushButton(self)
        self.export_b.setText('Export Plot Data to CSV')
        self.export_b.clicked.connect(self.exportCSV)

        ## Formatting Dock Area
        layout.addWidget(dock_area)
        layout.addWidget(self.ret_label)
        layout.addWidget(self.ret_b)
        layout.addWidget(self.plot_b)
        layout.addWidget(self.export_b)
        layout.addWidget(self.exit_b)
        self.dock1.addWidget(self.widget_one)
        self.dock2.addWidget(self.widget_two)
        self.setGeometry(100,100,900,600)

        ## Connect Date Filter Buttons to Fx
        self.widget_one.startDate_filter.dateChanged.connect(self.onStartDateChanged)
        self.widget_one.endDate_filter.dateChanged.connect(self.onEndDateChanged)

        ## Connect Filters to Fx
        self.widget_one.storefront_filter.activated.connect(self.updateFilters)
        self.widget_one.partner_filter.activated.connect(self.updateFilters)
        self.widget_one.brand_filter.activated.connect(self.updateFilters)
        self.widget_one.category_filter.activated.connect(self.updateFilters)
        self.widget_one.type_filter.activated.connect(self.updateFilters)
        self.widget_one.subType_filter.activated.connect(self.updateFilters)
        self.widget_one.orderType_filter.activated.connect(self.updateFilters)
        self.widget_one.status_filter.activated.connect(self.updateFilters)
        self.widget_one.province_filter.activated.connect(self.updateFilters)

        ## Connect Reset Filters button to Fx 
        self.widget_one.reset_b.clicked.connect(self.resetFilters)

        ## Set Initial Filters
        self.filters = {'report':'Revenue',
                        'storefront_name':'All',
                        'partner':'All',
                        'brand':'All',
                        'product_category':'All',
                        'product_type':'All',
                        'product_subtype':'All',
                        'order_type':'All',
                        'order_status':'All',
                        'province':'All',
                        'start_date':(datetime.today()-relativedelta(years=1)).strftime('%Y-%m-%d'),
                        'end_date':datetime.today().strftime('%Y-%m-%d')}
    

    def onStartDateChanged(self,newDate):
        self.filters['start_date'] = newDate.toString("yyyy-MM-dd")
    

    def onEndDateChanged(self,newDate):
        self.filters['end_date'] = newDate.toString("yyyy-MM-dd")
    

    def retData(self):
        self.ret_label.setText('Retrieving Data...')
        creds = ret_creds()
        try:
            self.rawdf = read_from_redshift(sql=self.sql,
                                            creds=creds,
                                            schema='reporting')
            self.popFilters()
            self.ret_label.setText('Data Retrieved Successfully!')
        except Exception as err:
            self.ret_label.setText('ERROR RETRIEVING DATA! Contact the Data Team at data@reservebar.com')
            print(str(err)[:250])
    

    def updateFilters(self):
        self.filters['storefront_name'] = self.widget_one.storefront_filter.currentText()
        self.filters['partner'] = self.widget_one.partner_filter.currentText()
        self.filters['brand'] = self.widget_one.brand_filter.currentText()
        self.filters['product_category'] = self.widget_one.category_filter.currentText()
        self.filters['product_type'] = self.widget_one.type_filter.currentText()
        self.filters['product_subtype'] = self.widget_one.subType_filter.currentText()
        self.filters['order_type'] = self.widget_one.orderType_filter.currentText()
        self.filters['order_status'] = self.widget_one.status_filter.currentText()
        self.filters['province'] = self.widget_one.province_filter.currentText()

        filterdf = self.rawdf
        filtered_fields = [filter_0 for filter_0 in self.filters if (self.filters[filter_0] != 'All') and 
                           (filter_0 not in ['start_date','end_date','report'])]
        unfiltered_fields = [filter_0 for filter_0 in self.filters if (self.filters[filter_0] == 'All') and 
                           (filter_0 not in ['start_date','end_date','report'])]

        for filter_0 in filtered_fields:
            filterdf = filterdf[filterdf[filter_0]==self.filters[filter_0]]
        
        filter_objects = {'storefront_name':self.widget_one.storefront_filter,
                          'partner':self.widget_one.partner_filter,
                          'brand':self.widget_one.brand_filter,
                          'product_category':self.widget_one.category_filter,
                          'product_type':self.widget_one.type_filter,
                          'product_subtype':self.widget_one.subType_filter,
                          'order_type':self.widget_one.orderType_filter,
                          'order_status':self.widget_one.status_filter,
                          'province':self.widget_one.province_filter}
        
        for filter_0 in unfiltered_fields:
            filter_objects[filter_0].clear()
            filter_objects[filter_0].addItem('All')
            filter_objects[filter_0].addItems(sorted(filter(None,list(set(filterdf[filter_0])))))
    

    def popFilters(self):
        self.widget_one.storefront_filter.addItems(sorted(filter(None,list(set(self.rawdf['storefront_name'])))))
        self.widget_one.partner_filter.addItems(sorted(filter(None,list(set(self.rawdf['partner'])))))
        self.widget_one.brand_filter.addItems(sorted(filter(None,list(set(self.rawdf['brand'])))))
        self.widget_one.category_filter.addItems(sorted(filter(None,list(set(self.rawdf['product_category'])))))
        self.widget_one.type_filter.addItems(sorted(filter(None,list(set(self.rawdf['product_type'])))))
        self.widget_one.subType_filter.addItems(sorted(filter(None,list(set(self.rawdf['product_subtype'])))))
        self.widget_one.orderType_filter.addItems(sorted(filter(None,list(set(self.rawdf['order_type'])))))
        self.widget_one.status_filter.addItems(sorted(filter(None,list(set(self.rawdf['order_status'])))))
        self.widget_one.province_filter.addItems(sorted(filter(None,list(set(self.rawdf['province'])))))
    

    def resetFilters(self):
        self.widget_one.startDate_filter.setDate(QtCore.QDate.currentDate().addYears(-1))
        self.widget_one.endDate_filter.setDate(QtCore.QDate.currentDate())

        self.widget_one.storefront_filter.clear()
        self.widget_one.partner_filter.clear()
        self.widget_one.brand_filter.clear()
        self.widget_one.category_filter.clear()
        self.widget_one.type_filter.clear()
        self.widget_one.subType_filter.clear()
        self.widget_one.orderType_filter.clear()
        self.widget_one.status_filter.clear()
        self.widget_one.province_filter.clear()

        self.widget_one.storefront_filter.addItem('All')
        self.widget_one.partner_filter.addItem('All')
        self.widget_one.brand_filter.addItem('All')
        self.widget_one.category_filter.addItem('All')
        self.widget_one.type_filter.addItem('All')
        self.widget_one.subType_filter.addItem('All')
        self.widget_one.orderType_filter.addItem('All')
        self.widget_one.status_filter.addItem('All')
        self.widget_one.province_filter.addItem('All')

        self.popFilters()


    def showPlot_test(self):
        df = px.data.tips()
        fig = px.box(df,
                     x="day",
                     y="total_bill",
                     color="smoker")
        fig.update_traces(quartilemethod="exclusive")
        self.widget_two.browser.setHtml(fig.to_html(include_plotlyjs='cdn'))
    

    def showPlot(self):
        try:
            self.filters['report'] = self.widget_one.report_type.currentText()
            self.filters['storefront_name'] = self.widget_one.storefront_filter.currentText()
            self.filters['partner'] = self.widget_one.partner_filter.currentText()
            self.filters['brand'] = self.widget_one.brand_filter.currentText()
            self.filters['product_category'] = self.widget_one.category_filter.currentText()
            self.filters['product_type'] = self.widget_one.type_filter.currentText()
            self.filters['product_subtype'] = self.widget_one.subType_filter.currentText()
            self.filters['order_type'] = self.widget_one.orderType_filter.currentText()
            self.filters['order_status'] = self.widget_one.status_filter.currentText()
            self.filters['province'] = self.widget_one.province_filter.currentText()

            ## Filter rawdf
            self.adf = self.rawdf[(self.rawdf['created_at']>datetime.strptime(self.filters['start_date'],"%Y-%m-%d").date()) &
                              (self.rawdf['created_at']<datetime.strptime(self.filters['end_date'],"%Y-%m-%d").date())]
            if self.filters['storefront_name'] != 'All':
                self.adf = self.adf[(self.rawdf['storefront_name']==self.filters['storefront_name'])]
            if self.filters['partner'] != 'All':
                self.adf = self.adf[(self.adf['partner']==self.filters['partner'])]
            if self.filters['brand'] != 'All':
                self.adf = self.adf[(self.adf['brand']==self.filters['brand'])]
            if self.filters['product_category'] != 'All':
                self.adf = self.adf[(self.adf['product_category']==self.filters['product_category'])]
            if self.filters['product_type'] != 'All':
                self.adf = self.adf[(self.adf['product_type']==self.filters['product_type'])]
            if self.filters['product_subtype'] != 'All':
                self.adf = self.adf[(self.adf['product_subtype']==self.filters['product_subtype'])]
            if self.filters['order_type'] != 'All':
                self.adf = self.adf[(self.adf['order_type']==self.filters['order_type'])]
            if self.filters['order_status'] != 'All':
                self.adf = self.adf[(self.adf['order_status']==self.filters['order_status'])]
            if self.filters['province'] != 'All':
                self.adf = self.adf[(self.adf['province']==self.filters['province'])]

            ## Report Chooser
            if self.filters['report'] == 'Revenue':
                self.showPlot_revenue()
            elif self.filters['report'] == 'Orders':
                self.showPlot_orders()
            elif self.filters['report'] == 'AOV':
                self.showPlot_aov()
            elif self.filters['report'] == 'Bottles':
                self.showPlot_bottles()
            elif self.filters['report'] == 'Customers':
                self.showPlot_customers()
        except Exception as err:
            print(str(err)[:250])
            self.ret_label.setText('Please use "Retrieve Data" first before trying to plot data')
    

    def showPlot_revenue(self):
        self.adf = self.adf[['created_at','revenue']]
        self.adf = self.adf.sort_values(by=['created_at'])
        self.adf = self.adf.groupby(['created_at']).sum().reset_index()
        roll_df = self.adf.rolling(7,min_periods=1).agg('mean')
        self.adf['rolling_revenue'] = roll_df['revenue']
        fig = px.line(self.adf,
                      x='created_at',
                      y=['revenue','rolling_revenue'],
                      labels={'rolling_revenue':'Rolling Revenue',
                              'revenue':'Revenue',
                              'created_at':'Order Creation',
                              'value':'Revenue'},
                      title='Revenue')
        newnames = {'rolling_revenue':'Rolling Revenue',
                    'revenue':'Revenue'}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name],
                                              legendgroup=newnames[t.name],
                                              hovertemplate=t.hovertemplate.replace(t.name,
                                                                                    newnames[t.name])))
        fig.update_layout(yaxis_tickprefix='$',yaxis_tickformat=',.2f',legend_title='Legend')
        self.widget_two.browser.setHtml(fig.to_html(include_plotlyjs='cdn'))
    

    def showPlot_orders(self):
        self.adf = self.adf[['created_at','order_number']]
        self.adf = self.adf.sort_values(by=['created_at'])
        self.adf = self.adf.groupby(['created_at']).agg({'order_number':pd.Series.nunique}).reset_index()
        roll_df = self.adf.rolling(7,min_periods=1).agg('mean')
        self.adf['rolling_order_number'] = roll_df['order_number']
        fig = px.line(self.adf,
                      x='created_at',
                      y=['order_number','rolling_order_number'],
                      labels={'rolling_order_number':'Rolling Order Count',
                              'order_number':'Order Count',
                              'created_at':'Order Creation',
                              'value':'Order Count'},
                      title='Orders')
        newnames = {'rolling_order_number':'Rolling Order Count',
                    'order_number':'Order Count'}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name],
                                              legendgroup=newnames[t.name],
                                              hovertemplate=t.hovertemplate.replace(t.name,
                                                                                    newnames[t.name])))
        fig.update_layout(legend_title='Legend')
        self.widget_two.browser.setHtml(fig.to_html(include_plotlyjs='cdn'))
    

    def showPlot_aov(self):
        self.adf = self.adf[['created_at','order_number','revenue']]
        self.adf = self.adf.sort_values(by=['created_at'])
        self.adf = self.adf.groupby(['created_at','order_number']).sum().reset_index()
        self.adf = self.adf.drop(columns=['order_number']).groupby(['created_at']).agg('mean').reset_index()
        roll_df = self.adf.rolling(7,min_periods=1).agg('mean')
        self.adf['rolling_revenue'] = roll_df['revenue']
        fig = px.line(self.adf,
                      x='created_at',
                      y=['revenue','rolling_revenue'],
                      labels={'rolling_revenue':'Rolling AOV',
                              'revenue':'AOV',
                              'created_at':'Order Creation',
                              'value':'AOV'},
                      title='Average Order Value')
        newnames = {'rolling_revenue':'Rolling AOV',
                    'revenue':'AOV'}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name],
                                              legendgroup=newnames[t.name],
                                              hovertemplate=t.hovertemplate.replace(t.name,
                                                                                    newnames[t.name])))
        fig.update_layout(yaxis_tickprefix='$',yaxis_tickformat=',.2f',legend_title='Legend')
        self.widget_two.browser.setHtml(fig.to_html(include_plotlyjs='cdn'))
    

    def showPlot_bottles(self):
        self.adf = self.adf[['created_at','quantity']]
        self.adf = self.adf.sort_values(by=['created_at'])
        self.adf = self.adf.groupby(['created_at']).sum().reset_index()
        roll_df = self.adf.rolling(7,min_periods=1).agg('mean')
        self.adf['rolling_quantity'] = roll_df['quantity']
        fig = px.line(self.adf,
                      x='created_at',
                      y=['quantity','rolling_quantity'],
                      labels={'rolling_quantity':'Rolling Bottle Count',
                              'quantity':'Bottle Count',
                              'created_at':'Order Creation',
                              'value':'Bottle Count'},
                      title='Bottle Count')
        newnames = {'rolling_quantity':'Rolling Bottle Count',
                    'quantity':'Bottle Count'}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name],
                                              legendgroup=newnames[t.name],
                                              hovertemplate=t.hovertemplate.replace(t.name,
                                                                                    newnames[t.name])))
        fig.update_layout(legend_title='Legend')
        self.widget_two.browser.setHtml(fig.to_html(include_plotlyjs='cdn'))
    

    def showPlot_customers(self):
        self.adf = self.adf[['created_at','customer_id']]
        self.adf = self.adf.sort_values(by=['created_at'])
        self.adf = self.adf.groupby(['created_at']).agg({'customer_id':pd.Series.nunique}).reset_index()
        roll_df = self.adf.rolling(7,min_periods=1).agg('mean')
        self.adf['rolling_customer_id'] = roll_df['customer_id']
        fig = px.line(self.adf,
                      x='created_at',
                      y=['customer_id','rolling_customer_id'],
                      labels={'rolling_customer_id':'Rolling Customer Count',
                              'customer_id':'Customer Count',
                              'created_at':'Order Creation',
                              'value':'Customer Count'},
                      title='Customer Count')
        newnames = {'rolling_customer_id':'Rolling Customer Count',
                    'customer_id':'Customer Count'}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name],
                                              legendgroup=newnames[t.name],
                                              hovertemplate=t.hovertemplate.replace(t.name,
                                                                                    newnames[t.name])))
        fig.update_layout(legend_title='Legend')
        self.widget_two.browser.setHtml(fig.to_html(include_plotlyjs='cdn'))


    def exportCSV(self):
        try:
            self.adf.to_csv('exported_data.csv',index=False,header=True)
            self.ret_label.setText('Data Exported Successfully!')
        except Exception as err:
            print(str(err)[:250])
            self.ret_label.setText('Data not exported. Make sure a plot is generated before attempting to export!')


## Filter Panel
class FilterWidget(QtWidgets.QWidget):
    ## Initialize Class
    def __init__(self,
                 parent):
        super(FilterWidget,self).__init__(parent)
        self.initWidget()
    

    ## Initialize Widget Elements
    def initWidget(self):
        ## Report Type
        report_label = QtWidgets.QLabel()
        report_label.setText('Report Type')
        self.report_type = QtWidgets.QComboBox()
        self.report_type.addItems(['Revenue',
                                   'Orders',
                                   'AOV',
                                   'Bottles',
                                   'Customers'])

        ## Filters
        self.storefront_filter = QtWidgets.QComboBox()
        self.storefront_filter.addItem('All')
        self.partner_filter = QtWidgets.QComboBox()
        self.partner_filter.addItem('All')
        self.brand_filter = QtWidgets.QComboBox()
        self.brand_filter.addItem('All')
        self.category_filter = QtWidgets.QComboBox()
        self.category_filter.addItem('All')
        self.type_filter = QtWidgets.QComboBox()
        self.type_filter.addItem('All')
        self.subType_filter = QtWidgets.QComboBox()
        self.subType_filter.addItem('All')
        self.orderType_filter = QtWidgets.QComboBox()
        self.orderType_filter.addItem('All')
        self.status_filter = QtWidgets.QComboBox()
        self.status_filter.addItem('All')
        self.startDate_filter = QtWidgets.QDateEdit()
        self.startDate_filter.setDate(QtCore.QDate.currentDate().addYears(-1))
        self.endDate_filter = QtWidgets.QDateEdit()
        self.endDate_filter.setDate(QtCore.QDate.currentDate())
        self.province_filter = QtWidgets.QComboBox()
        self.province_filter.addItem('All')

        ## Labels
        storefront_label = QtWidgets.QLabel()
        storefront_label.setText('Storefront')
        partner_label = QtWidgets.QLabel()
        partner_label.setText('Partner')
        brand_label = QtWidgets.QLabel()
        brand_label.setText('Brand')
        category_label = QtWidgets.QLabel()
        category_label.setText('Product Category')
        type_label = QtWidgets.QLabel()
        type_label.setText('Product Type')
        subType_label = QtWidgets.QLabel()
        subType_label.setText('Product Sub-type')
        orderType_label = QtWidgets.QLabel()
        orderType_label.setText('Order Type')
        status_label = QtWidgets.QLabel()
        status_label.setText('Order Status')
        startDate_label = QtWidgets.QLabel()
        startDate_label.setText('Start Date')
        endDate_label = QtWidgets.QLabel()
        endDate_label.setText('End Date')
        province_label = QtWidgets.QLabel()
        province_label.setText('State/Province')

        ## Reset Button
        self.reset_b = QtWidgets.QPushButton(self)
        self.reset_b.setText('Reset Filters')

        ## Layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.reset_b)
        layout.addWidget(report_label)
        layout.addWidget(self.report_type)
        layout.addWidget(startDate_label)
        layout.addWidget(self.startDate_filter)
        layout.addWidget(endDate_label)
        layout.addWidget(self.endDate_filter)
        layout.addWidget(storefront_label)
        layout.addWidget(self.storefront_filter)
        layout.addWidget(partner_label)
        layout.addWidget(self.partner_filter)
        layout.addWidget(brand_label)
        layout.addWidget(self.brand_filter)
        layout.addWidget(category_label)
        layout.addWidget(self.category_filter)
        layout.addWidget(type_label)
        layout.addWidget(self.type_filter)
        layout.addWidget(subType_label)
        layout.addWidget(self.subType_filter)
        layout.addWidget(orderType_label)
        layout.addWidget(self.orderType_filter)
        layout.addWidget(status_label)
        layout.addWidget(self.status_filter)
        layout.addWidget(province_label)
        layout.addWidget(self.province_filter)


## Plotly Dashboard Panel
class PlotlyWidget(QtWidgets.QWidget):
    ## Initialize Class
    def __init__(self,
                 parent):
        super(PlotlyWidget,self).__init__(parent)
        self.initWidget()
    

    ## Initialize Widget Elements
    def initWidget(self):
        self.browser = QtWebEngineWidgets.QWebEngineView(self)
        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.addWidget(self.browser)


## Retrieve Credentials if Exist
def ret_creds():
    """
    Args:
    none

    Returns:
    creds - dictionary of credentials needed for Redshift access
    """
    print('Retrieving credentials...')
    if exists('creds.pkl'):
        creds = pload(open('creds.pkl','rb'))
    else:
        raise Exception('No credentials found')
    print('Credentials retrieved.')
    return creds


## Create Redshift connection from credentials
def bld_cnxn(creds):
    """
    Args:
    creds(req) - dictionary of credentials needed for Redshift access

    Returns:
    client - Redshift connection engine
    """
    print('Building Redshift connection...')
    req_fields = ['redshift_username',
                  'redshift_password',
                  'redshift_host',
                  'redshift_port',
                  'redshift_database']
    for xx in req_fields:
        if xx not in creds:
            raise Exception(f'Missing required field: {xx}')
    rs_un = creds['redshift_username']
    rs_pw = creds['redshift_password']
    rs_host = creds['redshift_host']
    rs_port = creds['redshift_port']
    rs_db = creds['redshift_database']
    engine = create_engine('postgresql+psycopg2://'+rs_un+":"+rs_pw+"@"+rs_host+
                          ":"+rs_port+"/"+rs_db)\
                          .execution_options(autocommit=True)
    print('Connected to database '+rs_db+' as '+rs_un)
    return engine


## Read data from Redshift
def read_from_redshift(sql:str,
                       creds:dict,
                       schema:str='reporting'):
    """
    Args:
    data(req) - Pandas dataframe of the data to be uploaded to Redshift
    tbl_nm(req) - string Redshift table name
    creds(req) - dictionary of credentials needed for Redshift access
    schema - string Redshift schema name

    Returns:
    none
    """
    engine = bld_cnxn(creds)
    try:
        data = pd.read_sql(sql,engine)
        print(f'Records read from Redshift successfully')
        engine.dispose()
        return data
    except Exception as err:
        print(f'Error reading SQL from schema {schema}')
        engine.dispose()
        raise Exception(str(err)[:250])


def chk_table_exists(table:str,
                     schema:str,
                     creds:dict):
    sql = f"""SELECT EXISTS (
SELECT * FROM pg_catalog.pg_class c
JOIN   pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE  n.nspname = '{schema}'
AND    c.relname = '{table}'
AND    c.relkind = 'r'    -- only tables
) as tbl_exists;
    """
    engine = bld_cnxn(creds)
    try:
        edf = pd.read_sql(sql,engine)
        tbl_exists = edf.iloc[0]['tbl_exists']
    except Exception as err:
        print(str(err)[:250])
        tbl_exists = False
    finally:
        engine.dispose()
    return


## Main Function
def window():
    app = QApplication(sys.argv)
    win = mainWindow()
    win.setWindowTitle('Interactive Dashboard Builder')
    win.show()
    sys.exit(app.exec_())


window()
