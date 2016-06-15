def iq_buy(tick, ws):
	# global buyprice
	ipdb.set_trace()
	obj = threads["thread_"+str(tick[0]['instrument_token'])]
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
	for i in range(49):
		buyprice.append(buyprice[0] + float(obj.dpr*(i+1)/float(obj.n)))

	sellprice = []

	# ipdb.set_trace()
	sellprice.append(buyprice[0]-obj.dpr/3.0)
	sellprice.append(buyprice[0]-obj.dpr/8.0)
	sellprice.append((buyprice[0]+buyprice[1])/2.0)
	wa = buyprice[0]+buyprice[1]+buyprice[2]
	qsum = obj.lots*3
	for i in range(3,50):
		wa = wa + buyprice[i]
		qsum = qsum + obj.lots
		sellprice.append(wa/qsum)


	qty=[]
	for i in range(50):
		qty.append(obj.lots)


	return
	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	print bid
	to_buy_i = obj.to_buy_i
	if to_buy_i >= len(buyprice):
		return
	if bid <= sellprice[to_buy_i]:
		obj.ws.close()
		threads.pop("thread_"+str(tick[0]['instrument_token']), None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if bid >= buyprice[to_buy_i]:
		# ipdb.set_trace()
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
			thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Buy Order' , ) )
			# print("Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, (str(e), "error message"))

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
					thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
					# print("Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, (str(e), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="SELL",order_type="SL-M",quantity=obj.curr_qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ("success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Modified' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))
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
				thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1


def multi_buy(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads["thread_"+str(tick[0]['instrument_token'])]
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

	# ipdb.set_trace()
	sellprice.append(buyprice[0]-obj.dpr/3.0)
	sellprice.append(buyprice[0]-obj.dpr/8.0)
	sellprice.append((buyprice[0]+buyprice[1])/2.0)
	wa = buyprice[0] + buyprice[1] + buyprice[2]
	qsum = 3.0
	for i in range(4,30):
		wa = wa + (buyprice[i-1]*qty[i-1])
		qsum = qsum + qty[i-1]
		sellprice.append(wa/qsum)
	

	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	print bid
	to_buy_i = obj.to_buy_i
	if bid <= sellprice[to_buy_i]:
		obj.ws.close()
		threads.pop("thread_"+str(tick[0]['instrument_token']), None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid >= buyprice[to_buy_i]:
		# ipdb.set_trace()
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
			thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Buy Order' , ) )
			# print("Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, (str(e), "error message"))

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
					thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
					# print("Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, (str(e), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="SELL",order_type="SL-M",quantity=obj.curr_qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ("success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Modified' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))
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
				thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1


def multi_buy_esl(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads["thread_"+str(tick[0]['instrument_token'])]
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

	# ipdb.set_trace()
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
	

	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	print bid
	to_buy_i = obj.to_buy_i
	if bid <= sellprice[to_buy_i]:
		obj.ws.close()
		threads.pop("thread_"+str(tick[0]['instrument_token']), None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid >= buyprice[to_buy_i]:
		# ipdb.set_trace()
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
			thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Buy Order' , ) )
			# print("Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, (str(e), "error message"))

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
					thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
					# print("Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, (str(e), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="SELL",order_type="SL-M",quantity=obj.curr_qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ("success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Modified' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))
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
				thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1

		
def dsp_buy(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads["thread_"+str(tick[0]['instrument_token'])]
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

	# ipdb.set_trace()
	sellprice.append(entry*qty[0] + buyprice[0]*obj.lots/15.0)
	wa = entry*qty[0] + buyprice[0]*obj.lots
	qsum = qty[0] + 5
	for i in range(1,30):
		wa = wa + (buyprice[i]*obj.lots)
		qsum = qsum + qty[i]
		sellprice.append(wa/qsum)
	

	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	print bid
	to_buy_i = obj.to_buy_i
	if bid <= sellprice[to_buy_i]:
		obj.ws.close()
		threads.pop("thread_"+str(tick[0]['instrument_token']), None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid >= buyprice[to_buy_i]:
		# ipdb.set_trace()
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
			thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Buy Order' , ) )
			# print("Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, (str(e), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="SELL",
									quantity=obj.curr_qty+5,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
					# print("Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, (str(e), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="SELL",order_type="SL-M",quantity=obj.curr_qty+5,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ("success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Modified' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="SELL",
								quantity=obj.curr_qty+5,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Sell Order Placed' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1


def iq_sell(tick, ws):
	# global buyprice
	# ipdb.set_trace()
	obj = threads["thread_"+str(tick[0]['instrument_token'])]
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	print "access_token = " + str(obj.access_token)
	kite = KiteConnect(api_key=trading_api.settings.API_KEY)
	# data = kite.request_access_token("request_token_here", secret="your_secret")
	# kite.set_access_token(data["access_token"])
	# print data["access_token"]
	kite.set_access_token(obj.access_token)

	buyprice = []
	buyprice.append(obj.buyprice1)
	for i in range(50):
		buyprice.append(buyprice[0] - float(obj.dpr*(i+1)/float(obj.n)))

	sellprice = []
	sellprice.append(buyprice[0]+obj.dpr/3.0)
	sellprice.append(buyprice[0]+obj.dpr/8.0)
	sellprice.append((buyprice[0]+buyprice[1])/2.0)
	wa = buyprice[0]+buyprice[1]+buyprice[2]
	qsum = obj.lots*3
	for i in range(3,50):
		wa = wa + buyprice[i]
		qsum = qsum + obj.lots
		sellprice.append(wa/qsum)

	qty=[]
	for i in range(50):
		qty.append(obj.lots)



	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	# print bid

	# print buyprice
	# print sellprice
	# # ws.close()
	# return


	to_buy_i = obj.to_buy_i
	if bid >= sellprice[to_buy_i]:
		obj.ws.close()
		threads.pop("thread_"+str(tick[0]['instrument_token']), None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid <= buyprice[to_buy_i]:
		# ipdb.set_trace()
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
			thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Sell Order' , ) )
			# print("Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, (str(e), "error message"))

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
					thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
					# print("Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, (str(e), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="BUY",order_type="SL-M",quantity=obj.curr_qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ("success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Modified' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))
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
				thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1





def multi_sell(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads["thread_"+str(tick[0]['instrument_token'])]
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

	# ipdb.set_trace()
	sellprice.append(buyprice[0]+obj.dpr/3.0)
	sellprice.append(buyprice[0]+obj.dpr/8.0)
	sellprice.append((buyprice[0]+buyprice[1])/2.0)
	wa = buyprice[0] + buyprice[1] + buyprice[2]
	qsum = 3.0
	for i in range(4,30):
		wa = wa + (buyprice[i-1]*qty[i-1])
		qsum = qsum + qty[i-1]
		sellprice.append(wa/qsum)
	
	
	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	print bid
	to_buy_i = obj.to_buy_i
	if bid >= sellprice[to_buy_i]:
		obj.ws.close()
		threads.pop("thread_"+str(tick[0]['instrument_token']), None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid <= buyprice[to_buy_i]:
		# ipdb.set_trace()
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
			thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Sell Order' , ) )
			# print("Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, (str(e), "error message"))

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
					thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
					# print("Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, (str(e), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="BUY",order_type="SL-M",quantity=obj.curr_qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ("success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Modified' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))
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
				thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1



def multi_sell_esl(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads["thread_"+str(tick[0]['instrument_token'])]
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

	# ipdb.set_trace()
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
	

	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	print bid
	if bid >= sellprice[to_buy_i]:
		obj.ws.close()
		threads.pop("thread_"+str(tick[0]['instrument_token']), None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid <= buyprice[to_buy_i]:
		# ipdb.set_trace()
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
			thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Sell Order' , ) )
			# print("Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, (str(e), "error message"))

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
					thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
					# print("Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, (str(e), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="BUY",order_type="SL-M",quantity=obj.curr_qty,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ("success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Modified' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))
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
				thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1


def dsp_sell(tick, ws):
	# global buyprice
	print tick[0]['last_price']
	# print tick[0]['last_price']
	# to_buy_i = 
	obj = threads["thread_"+str(tick[0]['instrument_token'])]
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

	# ipdb.set_trace()
	sellprice.append(entry*qty[0] + buyprice[0]*obj.lots/15.0)
	wa = entry*qty[0] + buyprice[0]*obj.lots
	qsum = qty[0] + 5
	for i in range(1,30):
		wa = wa + (buyprice[i]*obj.lots)
		qsum = qsum + qty[i]
		sellprice.append(wa/qsum)
	
	

	bid = tick[0]['last_price']
	# to_buy = buyprice[0]
	print bid
	to_buy_i = obj.to_buy_i
	if bid >= sellprice[to_buy_i]:
		obj.ws.close()
		threads.pop("thread_"+str(tick[0]['instrument_token']), None)
		return
	if to_buy_i >= obj.max_buy:
		return
	if to_buy_i >= len(buyprice):
		return
	if bid <= buyprice[to_buy_i]:
		# ipdb.set_trace()
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
			thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(order_id) + ", price: " + str(buyprice[to_buy_i]),'Sell Order' , ) )
			# print("Order placed. ID is", order_id)
		except Exception as e:
			print str(e)
			thread.start_new_thread(send_mail, (str(e), "error message"))

		obj.curr_qty = obj.curr_qty + qty[to_buy_i]

		if obj.order_id:
			try:
				order = kite.orders(order_id=obj.order_id)
			except:
				try:
					obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
									exchange=obj.exchange,
									transaction_type="BUY",
									quantity=obj.curr_qty + 5,
									order_type="SL-M",
									product=obj.product_type,
									trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

					print "success placed sell" + str(obj.order_id)
					#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
					#email.send()
					thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
					# print("Order placed. ID is", order_id)
				except Exception as e:
					print str(e)
					thread.start_new_thread(send_mail, (str(e), "error message"))
			try:
				obj.order_id = kite.order_modify(str(obj.order_id),trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize), tradingsymbol=obj.symbol,exchange=obj.exchange,transaction_type="BUY",order_type="SL-M",quantity=obj.curr_qty+5,product=obj.product_type)

				print "success modified" + str(obj.order_id)
				#email = #emailMessage('Sell Order Modified', "success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["stockforindia@gmail.com"])
				#email.send()
				thread.start_new_thread( send_mail, ("success, order modified. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Modified' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))
		else:
			try:
				obj.order_id = kite.order_place(tradingsymbol=obj.symbol,
								exchange=obj.exchange,
								transaction_type="BUY",
								quantity=obj.curr_qty+5,
								order_type="SL-M",
								product=obj.product_type,
								trigger_price=myround(sellprice[to_buy_i],base=obj.ticksize))

				print "success placed sell" + str(obj.order_id)
				#email = #emailMessage('Sell Order Placed', "success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]), to=["akshay12489@yahoo.co.in"])
				#email.send()
				thread.start_new_thread( send_mail, ("success, order placed. Order Id = " + str(obj.order_id) + ", price: " + str(sellprice[to_buy_i]),'Buy(SL) Order Placed' , ) )
				# print("Order placed. ID is", order_id)
			except Exception as e:
				print str(e)
				thread.start_new_thread(send_mail, (str(e), "error message"))


		# place sl order at sellprice[to_buy_i]
		obj.to_buy_i = obj.to_buy_i + 1