import streamlit as st
import pandas as pd
from datetime import datetime
import calendar

class Dashboard:
    def __init__(self, client):
        self.client = client

        self.set_style()
        self.data = self.load_data(self.client)
    
    def set_style(self):
        hide_streamlit_style = """
                    <style>
                    #MainMenu {visibility: hidden;}
                    footer {visibility: hidden;}
                    </style>
                    """
        st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    def load_data(self, client, **kwargs):
        df = pd.read_csv('moyer_censored.csv')
        df = df.loc[df['Client'] == client]
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['Month Name'] = [calendar.month_name[i] for i in df['Month']]
        df['Month Name Year'] = df['Month Name'] + ', ' + df['Year'].astype(str)
        df['Month-Year'] = df['Month'].astype(str) + '-' + df['Year'].astype(str)

        return df

    def filter_data(self, timeperiod):
        df = self.data.loc[self.data['Month Name Year'] == timeperiod]
        
        return df

    def load_expense_report_v1(self, timeperiod):
        df = self.data[['Truck#', 'Serial#', 'Invoice#', 'Dollar', 'Month Name Year', 'Date']]
        df['Date'] = df['Date'].dt.strftime('%m/%d')
        df = df.loc[df['Month Name Year'] == timeperiod]
        df = df[['Truck#', 'Serial#', 'Invoice#', 'Dollar', 'Date']]

        pivoted = pd.pivot_table(df, values='Dollar', index=['Invoice#', 'Date'], columns='Truck#', aggfunc='sum')
        pivoted = pivoted.applymap(lambda x:  "${:,.2f}".format(x))
        self.pivoted = pivoted.replace("$nan", "").reset_index().sort_values('Date')

        self.alt_background_days = self.pivoted['Date'].unique()[::2]
        styled_df = self.pivoted.style.applymap(self.highlight_cells)

        return styled_df

    def load_expense_report_v2(self, timeperiod):
        df = self.data[['Truck#', 'Serial#', 'Dollar', 'Date', 'Month Name Year']]
        df['Date'] = df['Date'].dt.strftime('%m/%d')
        df = df.loc[df['Month Name Year'] == timeperiod]
        df = df[['Truck#', 'Serial#', 'Dollar', 'Date']]

        pivoted = pd.pivot_table(df, values='Dollar', index=['Truck#', 'Serial#'], columns='Date', aggfunc='sum')
        pivoted = pivoted.applymap(lambda x:  "${:,.2f}".format(x))
        pivoted = pivoted.replace("$nan", "")

        return pivoted
         
    def highlight_cells(self, val):
        if val in self.alt_background_days:
            return 'background-color: lightgrey'
        else:
            return ''

    def generate_dashbord(self):

        st.sidebar.header('Moyer Equipment Repair LLC')

        st.sidebar.subheader(self.client)

        timeperiod_choice = st.sidebar.selectbox(
            'Time Period',
            self.data[['Month Name Year', 'Date']].sort_values('Date', ascending=False)['Month Name Year'].drop_duplicates()
        )

        filtered_data = self.filter_data(timeperiod_choice)

        st.subheader(filtered_data['Month Name Year'].unique().item())

        #settings_bar = st.sidebar.subheader(current_month)

        #with st.sidebar:
        #    st.subheader(current_month)

        kpi1, kpi2, kpi3 = st.columns(3)

        kpi1.metric(
            label='Total Expenses',
            value="${:,.2f}".format(filtered_data['Dollar'].sum())
        )

        kpi2.metric(
            label='Trucks',
            value=len(filtered_data['Truck#'].unique())
        )

        if len(filtered_data['Truck#'].unique()) == 0:
            avg_truck_expense = 0
        else:
            avg_truck_expense = "${:,.2f}".format(filtered_data['Dollar'].sum() / len(filtered_data['Truck#'].unique()))

        kpi3.metric(
            label='AVG Truck Expense',
            value=avg_truck_expense
        )

        #st.line_chart(self.data.groupby(['Month Name Year'])['Dollar'].sum(),
        #             color='#F88379')
        
        #st.dataframe(self.data.groupby(['Month-Year','Month Name Year'])['Dollar'].sum())

        st.divider()

        st.subheader('Expense Reports')

        expense_report_v1 = self.load_expense_report_v1(timeperiod_choice)
        expense_report_v2 = self.load_expense_report_v2(timeperiod_choice)

        on = st.toggle('See Invoice Breakdown')
        placeholder = st.empty()
        if on:
            #st.write(expense_report_v1.to_html(), unsafe_allow_html=True)
            st.table(expense_report_v1)
            placeholder.empty()

        else:
            placeholder = st.table(expense_report_v2.reset_index())
