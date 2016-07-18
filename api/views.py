from django.shortcuts import render
import requests
from django.template import Context
from django.http import *
from django.template.loader import get_template
from django.views.decorators.csrf import *
import json
import ipdb
import trading_api.settings
from kiteconnect import WebSocket
from kiteconnect import KiteConnect
from ApiClass import *
from django.core.mail import EmailMessage
import csv
from models import *
from django.http import JsonResponse
import thread
from django.core.mail import send_mail as sm
# from strategies import *
# Create your views here.

def mon_buy(tick, ws):
	# global buyprice
	# #ipdb.set_trace()
	obj = threads_ws[ws]
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(10):
		buyprice.append(buyprice[0] + float(obj.dpr*(i+1)/float(obj.n)))

	sellprice = []
	qty=[]
	for i in range(3):
		qty.append(obj.lots)

	# #ipdb.set_trace()
	sellprice.append(buyprice[0]-obj.dpr/3.0)
	sellprice.append(buyprice[0]-obj.dpr/8.0)
	sellprice.append((buyprice[0]+buyprice[1])/2.0)
	wa = (buyprice[0]+buyprice[1]+buyprice[2])*obj.lots
	qsum = obj.lots*3
	for i in range(3,10):
		wa = wa + buyprice[i]*qsum
		qty.append(qsum)
		qsum = qsum*2
		sellprice.append(wa/qsum)


	# print buyprice
	# print sellprice
	if tick[0]['last_price'] <= 0.0:
		return
	# return
	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	#print bid
	to_buy_i = obj.to_buy_i
	# print sellprice
	# print qty
	# return
	if to_buy_i >= len(buyprice):
		return
	if bid <= sellprice[to_buy_i-1] and to_buy_i > 0:
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(obj.symbol)+' stopped which was running on '+obj.st + " due to SL. The values were: bid:" + str(bid) + " and SL: " + str(sellprice[to_buy_i]),'Symbol Stopped' , ) )
		threads.pop("thread_"+str(tick[0]['instrument_token'])+'$'+obj.st, None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if bid >= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "buying " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="BUY",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Buy Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="SELL",
									quantity=obj.curr_qty,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(obj.curr_qty) + " Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
					# print(" Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="SELL",order_type="SL-M",quantity=obj.curr_qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order modified. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Modified' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="SELL",
								quantity=obj.curr_qty,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order placed. "+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1


def iq_buy(tick, ws):
	# global buyprice
	# #ipdb.set_trace()
	obj = threads_ws[ws]
	if tick[0]['last_price'] <= 0.0:
		return
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(99):
		buyprice.append(buyprice[0] + float(obj.dpr*(i+1)/float(obj.n)))

	sellprice = []

	# #ipdb.set_trace()
	sellprice.append(buyprice[0]-obj.dpr/3.0)
	sellprice.append(buyprice[0])
	sellprice.append(buyprice[1])
	wa = buyprice[0]+buyprice[1]+buyprice[2]
	qsum = obj.lots*3
	for i in range(3,100):
		wa = wa + buyprice[i]
		qsum = qsum + obj.lots
		sellprice.append(wa/qsum)


	qty=[]
	for i in range(100):
		qty.append(obj.lots)


	# return
	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	#print bid
	to_buy_i = obj.to_buy_i
	if to_buy_i >= len(buyprice):
		return
	if bid <= sellprice[to_buy_i-1] and to_buy_i > 0:
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(obj.symbol)+' stopped which was running on '+obj.st + " due to SL. The values were: bid:" + str(bid) + " and SL: " + str(sellprice[to_buy_i]),'Symbol Stopped' , ) )
		threads.pop("thread_"+str(tick[0]['instrument_token'])+'$'+obj.st, None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if bid >= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "buying " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="BUY",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Buy Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="SELL",
									quantity=obj.curr_qty,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(obj.curr_qty) + " Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
					# print(" Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="SELL",order_type="SL-M",quantity=obj.curr_qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order modified. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Modified' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="SELL",
								quantity=obj.curr_qty,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order placed. "+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1


def multi_buy(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads_ws[ws]
	if tick[0]['last_price'] <= 0.0:
		return
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(29):
		buyprice.append(buyprice[0] + float(obj.dpr*(i+1)/float(obj.n)))

	qty=[]
	for i in range(6):
		qty.append(obj.lots)

	for i in range(5):
		qty.append(3*obj.lots)
	
	for i in range(5):
		qty.append(9*obj.lots)
	

	for i in range(13):
		qty.append(18*obj.lots)
	


	sellprice = []

	# #ipdb.set_trace()
	sellprice.append(buyprice[0]-obj.dpr/3.0)
	sellprice.append(buyprice[0]-obj.dpr/8.0)
	sellprice.append((buyprice[0]+buyprice[1])/2.0)
	wa = (buyprice[0] + buyprice[1] + buyprice[2])*obj.lots
	qsum = 3.0*(obj.lots)
	for i in range(4,30):
		wa = wa + (buyprice[i-1]*qty[i-1])
		qsum = qsum + qty[i-1]
		sellprice.append(wa/qsum)
	

	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	#print bid
	# print sellprice
	# return
	to_buy_i = obj.to_buy_i
	if bid <= sellprice[to_buy_i-1] and to_buy_i > 0:
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(obj.symbol)+' stopped which was running on '+obj.st + " due to SL. The values were: bid:" + str(bid) + " and SL: " + str(sellprice[to_buy_i]),'Symbol Stopped' , ) )
		threads.pop("thread_"+str(tick[0]['instrument_token'])+'$'+obj.st, None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid >= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "buying " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="BUY",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Buy Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="SELL",
									quantity=obj.curr_qty,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(obj.curr_qty) + " Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
					# print(" Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="SELL",order_type="SL-M",quantity=obj.curr_qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order modified. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Modified' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="SELL",
								quantity=obj.curr_qty,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order placed. "+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1

def multi_dsp_buy(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads_ws[ws]
	if tick[0]['last_price'] <= 0.0:
		return
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(29):
		buyprice.append(buyprice[0] + float(obj.dpr*(i+1)/float(obj.n)))

	qty=[]
	for i in range(5):
		qty.append(obj.lots)

	for i in range(5):
		qty.append(3*obj.lots)
	
	for i in range(5):
		qty.append(9*obj.lots)
	

	for i in range(13):
		qty.append(18*obj.lots)
	

	sellprice = []

	# #ipdb.set_trace()
	sellprice.append((obj.entry*obj.qty + buyprice[0]*qty[0])/(qty[0] + obj.qty))
	wa = obj.entry*obj.qty + buyprice[0]*obj.lots
	qsum = qty[0] + obj.qty
	for i in range(1,28):
		wa = wa + (buyprice[i]*qty[i])
		qsum = qsum + qty[i]
		sellprice.append(wa/qsum)


	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	#print bid
	to_buy_i = obj.to_buy_i
	if bid <= sellprice[to_buy_i-1] and to_buy_i > 0:
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(obj.symbol)+' stopped which was running on '+obj.st + " due to SL. The values were: bid:" + str(bid) + " and SL: " + str(sellprice[to_buy_i]),'Symbol Stopped' , ) )
		threads.pop("thread_"+str(tick[0]['instrument_token'])+'$'+obj.st, None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid >= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "buying " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="BUY",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Buy Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="SELL",
									quantity=obj.curr_qty + obj.qty,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(obj.curr_qty + obj.qty) + " Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
					# print(" Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="SELL",order_type="SL-M",quantity=obj.curr_qty + obj.qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order modified. Qty:"+str(obj.curr_qty + obj.qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Modified' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="SELL",
								quantity=obj.curr_qty + obj.qty,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order placed. "+str(obj.curr_qty + obj.qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1


def multi_buy_esl(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads_ws[ws]
	if tick[0]['last_price'] <= 0.0:
		return
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(29):
		buyprice.append(buyprice[0] + float(obj.dpr*(i+1)/float(obj.n)))

	qty=[]
	for i in range(6):
		qty.append(obj.lots)

	for i in range(5):
		qty.append(3*obj.lots)
	
	for i in range(5):
		qty.append(9*obj.lots)
	

	for i in range(13):
		qty.append(18*obj.lots)
	


	sellprice = []

	sellprice.append(buyprice[0]-obj.dpr/3.0)
	sellprice.append(buyprice[0]-obj.dpr/8.0)
	sellprice.append(buyprice[0])
	sellprice.append((buyprice[0]+buyprice[1])/2.0)
	sellprice.append(buyprice[1])
	wa = buyprice[0] + buyprice[1] + buyprice[2]
	qsum = 3.0 * obj.lots
	for i in range(6,30):
		wa = wa + (buyprice[i-1]*qty[i-1])
		qsum = qsum + qty[i-1]
		sellprice.append(wa/qsum)
	
	# #ipdb.set_trace()

	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	#print bid
	to_buy_i = obj.to_buy_i
	if bid <= sellprice[to_buy_i-1] and to_buy_i > 0:
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(obj.symbol)+' stopped which was running on '+obj.st + " due to SL. The values were: bid:" + str(bid) + " and SL: " + str(sellprice[to_buy_i]),'Symbol Stopped' , ) )
		threads.pop("thread_"+str(tick[0]['instrument_token'])+'$'+obj.st, None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid >= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "buying " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="BUY",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Buy Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="SELL",
									quantity=obj.curr_qty,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(obj.curr_qty) + " Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
					# print(" Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="SELL",order_type="SL-M",quantity=obj.curr_qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order modified. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Modified' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="SELL",
								quantity=obj.curr_qty,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order placed. "+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1

		
def dsp_buy(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads_ws[ws]
	if tick[0]['last_price'] <= 0.0:
		return
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(29):
		buyprice.append(buyprice[0] + float(obj.dpr*(i+1)/float(obj.n)))

	qty=[]
	for i in range(30):
		qty.append(obj.lots)

	sellprice = []

	# #ipdb.set_trace()
	sellprice.append((obj.entry*obj.qty + buyprice[0]*obj.lots)/(qty[0] + obj.qty))
	wa = obj.entry*obj.qty + buyprice[0]*obj.lots
	qsum = qty[0] + obj.qty
	for i in range(1,30):
		wa = wa + (buyprice[i]*obj.lots)
		qsum = qsum + qty[i]
		sellprice.append(wa/qsum)
	

	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	#print bid
	# return
	# #ipdb.set_trace()
	to_buy_i = obj.to_buy_i
	if bid <= sellprice[to_buy_i-1] and to_buy_i > 0:
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(obj.symbol)+' stopped which was running on '+obj.st + " due to SL. The values were: bid:" + str(bid) + " and SL: " + str(sellprice[to_buy_i]),'Symbol Stopped' , ) )
		threads.pop("thread_"+str(tick[0]['instrument_token'])+'$'+obj.st, None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid >= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "buying " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="BUY",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Buy Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="SELL",
									quantity=obj.curr_qty+obj.qty,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(obj.curr_qty+obj.qty) + " Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
					# print(" Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="SELL",order_type="SL-M",quantity=obj.curr_qty+obj.qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order modified. Qty:"+str(obj.curr_qty+obj.qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Modified' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="SELL",
								quantity=obj.curr_qty+obj.qty,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:"+str(obj.curr_qty+obj.qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1

def mon_dsp_buy(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads_ws[ws]
	if tick[0]['last_price'] <= 0.0:
		return
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(29):
		buyprice.append(buyprice[0] + float(obj.dpr*(i+1)/float(obj.n)))

	qty=[]
	qty.append(obj.lots)
	qty.append(qty[0]+obj.qty)
	for i in range(2,30):
		qty.append(qty[i-1]*2)

	sellprice = []

	# #ipdb.set_trace()
	sellprice.append((obj.entry*obj.qty + buyprice[0]*obj.lots)/(qty[0] + obj.qty))
	wa = obj.entry*obj.qty + buyprice[0]*obj.lots
	qsum = qty[0] + obj.qty
	for i in range(1,30):
		wa = wa + (buyprice[i]*qty[i])
		qsum = qsum + qty[i]
		sellprice.append(wa/qsum)
	

	bid = tick[0]['last_price']
	# print qty
	# print sellprice
	# return
	# to_buy = buyprice[0]
	#print bid
	# return
	# #ipdb.set_trace()
	to_buy_i = obj.to_buy_i
	if bid <= sellprice[to_buy_i-1] and to_buy_i > 0:
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(obj.symbol)+' stopped which was running on '+obj.st + " due to SL. The values were: bid:" + str(bid) + " and SL: " + str(sellprice[to_buy_i]),'Symbol Stopped' , ) )
		threads.pop("thread_"+str(tick[0]['instrument_token'])+'$'+obj.st, None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid >= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "buying " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="BUY",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Buy Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="SELL",
									quantity=obj.curr_qty+obj.qty,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(obj.curr_qty+obj.qty) + " Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
					# print(" Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="SELL",order_type="SL-M",quantity=obj.curr_qty+obj.qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order modified. Qty:"+str(obj.curr_qty+obj.qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Modified' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="SELL",
								quantity=obj.curr_qty+obj.qty,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:"+str(obj.curr_qty+obj.qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1

def mon_dsp_sell(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads_ws[ws]
	if tick[0]['last_price'] <= 0.0:
		return
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(29):
		buyprice.append(buyprice[0] - float(obj.dpr*(i+1)/float(obj.n)))

	qty=[]
	qty.append(obj.lots)
	qty.append(qty[0]+obj.qty)
	for i in range(2,30):
		qty.append(qty[i-1]*2)

	sellprice = []

	# #ipdb.set_trace()
	sellprice.append((obj.entry*obj.qty + buyprice[0]*obj.lots)/(qty[0] + obj.qty))
	wa = obj.entry*obj.qty + buyprice[0]*obj.lots
	qsum = qty[0] + obj.qty
	for i in range(1,30):
		wa = wa + (buyprice[i]*qty[i])
		qsum = qsum + qty[i]
		sellprice.append(wa/qsum)
	

	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	#print bid
	# return
	# #ipdb.set_trace()
	to_buy_i = obj.to_buy_i
	if bid >= sellprice[to_buy_i-1] and to_buy_i > 0:
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(obj.symbol)+' stopped which was running on '+obj.st + " due to SL. The values were: bid:" + str(bid) + " and SL: " + str(sellprice[to_buy_i]),'Symbol Stopped' , ) )
		threads.pop("thread_"+str(tick[0]['instrument_token'])+'$'+obj.st, None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid <= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "buying " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="SELL",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Buy Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="BUY",
									quantity=obj.curr_qty+obj.qty,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(obj.curr_qty+obj.qty) + " Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
					# print(" Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="BUY",order_type="SL-M",quantity=obj.curr_qty+obj.qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order modified. Qty:"+str(obj.curr_qty+obj.qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Modified' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="BUY",
								quantity=obj.curr_qty+obj.qty,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:"+str(obj.curr_qty+obj.qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1


def mon_sell(tick, ws):
	# global buyprice
	# #ipdb.set_trace()
	obj = threads_ws[ws]
	if tick[0]['last_price'] <= 0.0:
		return
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	# print "access_token = " + str(obj.access_token)
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(10):
		buyprice.append(buyprice[0] - float(obj.dpr*(i+1)/float(obj.n)))

	qty=[]
	for i in range(3):
		qty.append(obj.lots)
	sellprice = []
	sellprice.append(buyprice[0]+obj.dpr/3.0)
	sellprice.append(buyprice[0]+obj.dpr/8.0)
	sellprice.append((buyprice[0]+buyprice[1])/2.0)
	wa = (buyprice[0]+buyprice[1]+buyprice[2])*obj.lots
	qsum = obj.lots*3
	for i in range(3,10):
		wa = wa + buyprice[i]*qsum
		qty.append(qsum)
		qsum = qsum*2
		sellprice.append(wa/qsum)




	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	# #print bid

	# #print buyprice
	# print sellprice
	# ws.close()
	# return


	to_buy_i = obj.to_buy_i
	if bid >= sellprice[to_buy_i-1] and to_buy_i > 0:
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(obj.symbol)+' stopped which was running on '+obj.st + " due to SL. The values were: bid:" + str(bid) + " and SL: " + str(sellprice[to_buy_i]),'Symbol Stopped' , ) )
		threads.pop("thread_"+str(tick[0]['instrument_token'])+'$'+obj.st, None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid <= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "selling " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="SELL",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. QTY:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Sell Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="BUY",
									quantity=obj.curr_qty,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
					# print(" Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="BUY",order_type="SL-M",quantity=obj.curr_qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order modified. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Modified' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="BUY",
								quantity=obj.curr_qty,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1


def iq_sell(tick, ws):
	# global buyprice
	# #ipdb.set_trace()
	obj = threads_ws[ws]
	if tick[0]['last_price'] <= 0.0:
		return
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	# print "access_token = " + str(obj.access_token)
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(100):
		buyprice.append(buyprice[0] - float(obj.dpr*(i+1)/float(obj.n)))

	sellprice = []
	sellprice.append(buyprice[0]+obj.dpr/3.0)
	sellprice.append(buyprice[0])
	sellprice.append(buyprice[1])
	wa = buyprice[0]+buyprice[1]+buyprice[2]
	qsum = obj.lots*3
	for i in range(3,100):
		wa = wa + buyprice[i]
		qsum = qsum + obj.lots
		sellprice.append(wa/qsum)

	qty=[]
	for i in range(100):
		qty.append(obj.lots)



	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	# #print bid

	# #print buyprice
	# print sellprice
	# ws.close()
	# return


	to_buy_i = obj.to_buy_i
	if bid >= sellprice[to_buy_i-1] and to_buy_i > 0:
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(obj.symbol)+' stopped which was running on '+obj.st + " due to SL. The values were: bid:" + str(bid) + " and SL: " + str(sellprice[to_buy_i]),'Symbol Stopped' , ) )
		threads.pop("thread_"+str(tick[0]['instrument_token'])+'$'+obj.st, None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid <= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "selling " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="SELL",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. QTY:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Sell Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="BUY",
									quantity=obj.curr_qty,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
					# print(" Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="BUY",order_type="SL-M",quantity=obj.curr_qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order modified. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Modified' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="BUY",
								quantity=obj.curr_qty,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1


def multi_sell(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads_ws[ws]
	if tick[0]['last_price'] <= 0.0:
		return
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(30):
		buyprice.append(buyprice[0] - float(obj.dpr*(i+1)/float(obj.n)))

	qty=[]
	for i in range(6):
		qty.append(obj.lots)

	for i in range(5):
		qty.append(3*obj.lots)
	
	for i in range(5):
		qty.append(9*obj.lots)
	

	for i in range(13):
		qty.append(18*obj.lots)

	sellprice = []

	# #ipdb.set_trace()
	sellprice.append(buyprice[0]+obj.dpr/3.0)
	sellprice.append(buyprice[0]+obj.dpr/8.0)
	sellprice.append((buyprice[0]+buyprice[1])/2.0)
	wa = (buyprice[0] + buyprice[1] + buyprice[2])*obj.lots
	qsum = 3.0*(obj.lots)
	for i in range(4,30):
		wa = wa + (buyprice[i-1]*qty[i-1])
		qsum = qsum + qty[i-1]
		sellprice.append(wa/qsum)
	
	
	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	#print bid
	to_buy_i = obj.to_buy_i
	if bid >= sellprice[to_buy_i-1] and to_buy_i > 0:
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(obj.symbol)+' stopped which was running on '+obj.st + " due to SL. The values were: bid:" + str(bid) + " and SL: " + str(sellprice[to_buy_i]),'Symbol Stopped' , ) )
		threads.pop("thread_"+str(tick[0]['instrument_token'])+'$'+obj.st, None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid <= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "selling " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="SELL",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. QTY:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Sell Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="BUY",
									quantity=obj.curr_qty,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
					# print(" Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="BUY",order_type="SL-M",quantity=obj.curr_qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order modified. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Modified' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="BUY",
								quantity=obj.curr_qty,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1


def multi_sell_esl(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads_ws[ws]
	if tick[0]['last_price'] <= 0.0:
		return
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(29):
		buyprice.append(buyprice[0] - float(obj.dpr*(i+1)/float(obj.n)))

	qty=[]
	for i in range(6):
		qty.append(obj.lots)

	for i in range(5):
		qty.append(3*obj.lots)
	
	for i in range(5):
		qty.append(9*obj.lots)
	

	for i in range(13):
		qty.append(18*obj.lots)
	


	sellprice = []

	sellprice.append(buyprice[0]+obj.dpr/3.0)
	sellprice.append(buyprice[0]+obj.dpr/8.0)
	sellprice.append(buyprice[0])
	sellprice.append((buyprice[0]+buyprice[1])/2.0)
	sellprice.append(buyprice[1])
	wa = buyprice[0] + buyprice[1] + buyprice[2]
	qsum = 3.0 * obj.lots
	for i in range(6,30):
		wa = wa + (buyprice[i-1]*qty[i-1])
		qsum = qsum + qty[i-1]
		sellprice.append(wa/qsum)
	
	#ipdb.set_trace()

	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	#print bid
	to_buy_i = obj.to_buy_i
	if bid >= sellprice[to_buy_i-1] and to_buy_i > 0:
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(obj.symbol)+' stopped which was running on '+obj.st + " due to SL. The values were: bid:" + str(bid) + " and SL: " + str(sellprice[to_buy_i]),'Symbol Stopped' , ) )
		threads.pop("thread_"+str(tick[0]['instrument_token'])+'$'+obj.st, None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid <= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "selling " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="SELL",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. QTY:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Sell Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="BUY",
									quantity=obj.curr_qty,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
					# print(" Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="BUY",order_type="SL-M",quantity=obj.curr_qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order modified. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Modified' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="BUY",
								quantity=obj.curr_qty,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:"+str(obj.curr_qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1


def dsp_sell(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads_ws[ws]
	if tick[0]['last_price'] <= 0.0:
		return
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(29):
		buyprice.append(buyprice[0] - float(obj.dpr*(i+1)/float(obj.n)))

	qty=[]
	for i in range(30):
		qty.append(obj.lots)

	sellprice = []

	# #ipdb.set_trace()
	sellprice.append((obj.entry*obj.qty + buyprice[0]*obj.lots)/(qty[0] + obj.qty))
	wa = obj.entry*obj.qty + buyprice[0]*obj.lots
	qsum = qty[0] + obj.qty
	for i in range(1,30):
		wa = wa + (buyprice[i]*obj.lots)
		qsum = qsum + qty[i]
		sellprice.append(wa/qsum)
	
	
	# #ipdb.set_trace()
	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	#print bid
	to_buy_i = obj.to_buy_i
	if bid >= sellprice[to_buy_i-1] and to_buy_i > 0:
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(obj.symbol)+' stopped which was running on '+obj.st + " due to SL. The values were: bid:" + str(bid) + " and SL: " + str(sellprice[to_buy_i]),'Symbol Stopped' , ) )
		threads.pop("thread_"+str(tick[0]['instrument_token'])+'$'+obj.st, None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid <= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "selling " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="SELL",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. QTY:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Sell Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="BUY",
									quantity=obj.curr_qty + obj.qty,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:"+str(obj.curr_qty+obj.qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
					# print(" Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="BUY",order_type="SL-M",quantity=obj.curr_qty+obj.qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order modified. Qty:"+str(obj.curr_qty+obj.qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Modified' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="BUY",
								quantity=obj.curr_qty+obj.qty,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:"+str(obj.curr_qty+obj.qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1

def multi_dsp_sell(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads_ws[ws]
	if tick[0]['last_price'] <= 0.0:
		return
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(29):
		buyprice.append(buyprice[0] - float(obj.dpr*(i+1)/float(obj.n)))

	qty=[]
	for i in range(5):
		qty.append(obj.lots)

	for i in range(5):
		qty.append(3*obj.lots)
	
	for i in range(5):
		qty.append(9*obj.lots)
	

	for i in range(13):
		qty.append(18*obj.lots)
	

	sellprice = []

	# #ipdb.set_trace()
	sellprice.append((obj.entry*obj.qty + buyprice[0]*qty[0])/(qty[0] + obj.qty))
	wa = obj.entry*obj.qty + buyprice[0]*obj.lots
	qsum = qty[0] + obj.qty
	for i in range(1,28):
		wa = wa + (buyprice[i]*qty[i])
		qsum = qsum + qty[i]
		sellprice.append(wa/qsum)


	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	#print bid
	to_buy_i = obj.to_buy_i
	if bid >= sellprice[to_buy_i-1] and to_buy_i > 0:
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(obj.symbol)+' stopped which was running on '+obj.st + " due to SL. The values were: bid:" + str(bid) + " and SL: " + str(sellprice[to_buy_i]),'Symbol Stopped' , ) )
		threads.pop("thread_"+str(tick[0]['instrument_token'])+'$'+obj.st, None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid <= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "buying " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="SELL",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Buy Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="BUY",
									quantity=obj.curr_qty + obj.qty,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(obj.curr_qty + obj.qty) + " Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
					# print(" Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="BUY",order_type="SL-M",quantity=obj.curr_qty + obj.qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order modified. Qty:"+str(obj.curr_qty + obj.qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Modified' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="BUY",
								quantity=obj.curr_qty + obj.qty,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ( obj, "success, order placed. "+str(obj.curr_qty + obj.qty)+" Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
				# print(" Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1

def iq_buy_nsl(tick, ws):
	# global buyprice
	# #ipdb.set_trace()
	obj = threads_ws[ws]
	if tick[0]['last_price'] <= 0.0:
		return
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(99):
		buyprice.append(buyprice[0] + float(obj.dpr*(i+1)/float(obj.n)))

	sellprice = []

	# #ipdb.set_trace()
	sellprice.append(buyprice[0]-obj.dpr/3.0)
	sellprice.append(buyprice[0])
	sellprice.append(buyprice[1])
	wa = buyprice[0]+buyprice[1]+buyprice[2]
	qsum = obj.lots*3
	for i in range(3,100):
		wa = wa + buyprice[i]
		qsum = qsum + obj.lots
		sellprice.append(wa/qsum)


	qty=[]
	for i in range(100):
		qty.append(obj.lots)


	# return
	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	#print bid
	to_buy_i = obj.to_buy_i
	if to_buy_i >= len(buyprice):
		return
	if to_buy_i >= obj.max_buy:
		return
	if bid >= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "buying " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="BUY",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. Qty:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Buy Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1


def iq_sell_nsl(tick, ws):
	# global buyprice
	# #ipdb.set_trace()
	obj = threads_ws[ws]
	if tick[0]['last_price'] <= 0.0:
		return
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	# print "access_token = " + str(obj.access_token)
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(100):
		buyprice.append(buyprice[0] - float(obj.dpr*(i+1)/float(obj.n)))

	sellprice = []
	sellprice.append(buyprice[0]+obj.dpr/3.0)
	sellprice.append(buyprice[0])
	sellprice.append(buyprice[1])
	wa = buyprice[0]+buyprice[1]+buyprice[2]
	qsum = obj.lots*3
	for i in range(3,100):
		wa = wa + buyprice[i]
		qsum = qsum + obj.lots
		sellprice.append(wa/qsum)

	qty=[]
	for i in range(100):
		qty.append(obj.lots)



	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	# #print bid

	# #print buyprice
	# print sellprice
	# ws.close()
	# return


	to_buy_i = obj.to_buy_i
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid <= buyprice[to_buy_i]:
		# #ipdb.set_trace()
		print "selling " + str(qty[to_buy_i]) + " stocks at " + str(bid) + " with SL = " + str(sellprice[to_buy_i])
		try:
			order_id = kite.order_place(tradingsymbol=obj.symbol,
							exchange=obj.exchange,
							transaction_type="SELL",
							quantity=qty[to_buy_i],
							order_type=obj.order_type,
							product=obj.product_type,
							price=myround(buyprice[to_buy_i],base=obj.ticksize))

			print "success, order placed. Order Id = " + str(order_id)
			#email = #emailMessage('Buy Order', "success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]), to=["stockforindia@gmail.com"])
			#email.send()
			thread.start_new_thread( send_mail, ( obj, "success, order placed. QTY:" + str(qty[to_buy_i]) + " Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Sell Order' , ) )
			# print(" Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, ( obj, str(e) + " sl:" + str(sellprice[to_buy_i]) + " and " + str(myround(sellprice[to_buy_i],base=obj.ticksize)), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1



threads = {}
threads_ws = {}
st = {}
st['iq_buy'] = iq_buy
st['iq_buy_nsl'] = iq_buy_nsl
st['mon_dsp_buy'] = mon_dsp_buy
st['mon_dsp_sell'] = mon_dsp_sell
st['multi_dsp_sell'] = multi_dsp_sell
st['mon_buy'] = mon_buy
st['iq_sell'] = iq_sell
st['iq_sell_nsl'] = iq_sell_nsl
st['mon_sell'] = mon_sell
st['multi_buy'] = multi_buy
st['multi_dsp_buy'] = multi_dsp_buy
st['multi_sell'] = multi_sell
st['multi_buy_esl'] = multi_buy_esl
st['multi_sell_esl'] = multi_sell_esl
st['dsp_buy'] = dsp_buy
st['dsp_sell'] = dsp_sell


def response(status, msg, *args):
	# args are tuples
	res = {}
	res['status'] = status
	res['msg'] = msg
	for arg in args:
		res[arg[0]] = arg[1]
	return HttpResponse(json.dumps(res,indent=4))

def myround(x, prec=2, base=.05):
  return round(base * round(float(x)/base),prec)



#	ws.close()
	# if work:
	# # 	place order here
	# # 	right now just testing so no order placed

	# 	if bid <= sellprice[to_buy_i-1] and to_buy_i > 0:
	# 		print "SL at " + str(sellprice[to_buy_i]) + "complete at " + str(datetime.utcnow().date()) +str(datetime.utcnow().time())
	# 		# to_buy_i = to_buy_i + 1
	# 		curr_qty = curr_qty + qty[to_buy_i]
	# 		work = False



@csrf_exempt
def home_st(request, strategy):
	if request.method == "POST":
		# ipdb.set_trace()
		global st
		if 'thread_' + request.POST['ins_token'] in threads:
			return response("failed", "already running")
		if "access_token" not in request.session:
			return response("failed", "access_token not set")
		kws = WebSocket(trading_api.settings.API_KEY, request.session["access_token"], trading_api.settings.LOGIN)
		def on_connect(ws):
			ws.subscribe([int(request.POST['ins_token'])])
			ws.set_mode(ws.MODE_FULL, [int(request.POST['ins_token'])])
		kws.on_connect = on_connect
		kws.on_tick = st[strategy]
		ws_obj = ApiClass(request.session["access_token"], request.POST.dict())
		#
		if "dsp" in strategy:
			ws_obj.set_dsp(request.POST['entry'], request.POST['qty'])
		try:
			kws.connect(threaded=True)
		except:
			return response("failed", "failed to connect")
		
		ws_obj.set_ws(kws)
		ws_obj.set_st(strategy)

		# threads['thread_' + ]
		# thread1 = ApiClass(request.session['access_token'],request.POST.dict())
		threads['thread_' + request.POST['ins_token'] + '$' + strategy] = ws_obj
		threads_ws[kws] = ws_obj
		# return render(request,'home.html')
		return HttpResponseRedirect('/api/home/' + strategy)
	if "dsp" not in strategy:
		return render(request, "home.html")
	else:
		return render(request,"dsp.html")


def home(request):
	global threads
	

		# thread1.start()
	# return HttpResponse("Hello, world")
	return render(request,'home.html')


# def test(request):
# 	global threads
# 	# email = EmailMessage('title', 'body', to=["tanmaydatta@gmail.com"])
# 	# email.send()
# 	send_mail("msg","subject")
# 	return HttpResponse(len(threads))

@csrf_exempt
def set_access(request):
	if request.method == "GET":
		return render(request, "set_access.html")
	elif request.method == "POST":
		try:
			access_token = request.POST['access_token']
			request.session['access_token'] = access_token
		except:
			return response("failed", "error storing access token")
		return response("success", "access_token stored successfully")
	else:
		return response("failed", "not a get/post request")


@csrf_exempt
def set_request(request):
	if request.method == "GET":
		return render(request, "set_request.html")
	elif request.method == "POST":
		try:
			try:
				request_token = request.POST['request_token']
			except:
				return response("failed", "request token not received")
			kite = KiteConnect(api_key=trading_api.settings.API_KEY)
			data = kite.request_access_token(request_token, secret=trading_api.settings.API_SECRET)
			request.session['access_token'] = data["access_token"]
			thread.start_new_thread( send_access, ( data["access_token"], ) )
		except Exception as e:
			return response("failed", "error storing access token: " + str(e))
		return response("success", "access_token stored successfully")
	else:
		return response("failed", "not a get/post request")


def running(request):
	global threads
	running_threads = []
	for key in threads:
		running_threads.append((threads[key].symbol,threads[key].ins_token, threads[key].st, threads[key].buyprice1))
	return render(request, "running.html", {"running":running_threads})


def stop(request, symbol):
	global threads
	global threads_ws
	# st = symbol.split('$')[1]
	symbol = "thread_" + symbol

	# #ipdb.set_trace()
	if symbol in threads:
		obj = threads[symbol]
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(symbol)+' stopped Manually','Symbol Stopped' , ) )
		threads.pop(symbol, None)
	else:
		return response("failed", "no such symbol running")

	return response("success", "successfully stopped")


def stop_all(request):
	global threads
	global threads_ws
	# st = symbol.split('$')[1]
	# symbol = "thread_" + symbol

	# #ipdb.set_trace()
	stops = threads.keys()
	for symbol in stops:
		obj = threads[symbol]
		obj.ws.close()
		thread.start_new_thread( send_mail, ( obj, str(symbol)+' stopped Manually','Symbol Stopped' , ) )
		threads.pop(symbol, None)

	return response("success", "successfully stopped")


def search(request,symbol):
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(request.session['access_token'])
	orders = kite.instruments()
	res=[]
	for order in orders:
		if symbol.lower() in order['tradingsymbol'].lower():
			res.append(order)
		# obj = Instruments(name=order['name'],symbol=order['tradingsymbol'],token=str(order['instrument_token']),exchange=order['exchange'],tick_size=str(order['tick_size']))
		# obj.save()

	# #ipdb.set_trace()
	# return response("success", "")
	return JsonResponse({"res":res})


def send_mail(obj, msg, subject):
	sm(subject + " " + obj.st, msg,"tanmaydatta@gmail.com" ,["stockforindia@gmail.com"],fail_silently=False)
	# sm(subject + " " + obj.st, msg,"tanmaydatta@gmail.com" ,["tanmaydatta@gmail.com"],fail_silently=False)
	#email.send()


def send_access(access_token):
	sm("access_token",str(access_token),"tanmaydatta@gmail.com" ,["stockforindia@gmail.com"],fail_silently=False)

def test(request):
	request.session['username'] = "tanmay"
	return HttpResponse("hello")