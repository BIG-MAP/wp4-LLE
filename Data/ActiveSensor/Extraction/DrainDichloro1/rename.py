import os
# Function to rename multiple files


def main():
	i = 0
	path = "."
	for test in os.listdir(path):
		print(test)
		if not os.path.isfile(test):
			for data in os.listdir(path+"/"+test):
				print(data)
				if not os.path.isfile(path+"/"+test+"/"+data):
					for i in range(169):
						source = "funnel"+str(i)+".jpg"
						destination = str(i) + ".jpg"
						if source in os.listdir(path+"/"+test+"/"+data+"/Images"):
							print(path+"/"+test+"/"+data+"/Images/"+source)
							print(path+"/"+test+"/"+data+"/Images/"+destination)
							os.rename(path+"/"+test+"/"+data+"/Images/"+source, path+"/"+test+"/"+data+"/Images/"+destination)
	#for i in range(169):
	#	source = "a"+str(i)+".jpg"
	#	destination ="funnel" + str(i) + ".jpg"
	#	if source in os.listdir(path):
	#		print(source)
	#		print(destination)
			#os.rename(source, destination)
		#my_source =path + filename
		#my_dest =path + my_dest
		# rename() function will
		# rename all the files


	#	i += 1
# Driver Code
if __name__ == '__main__':
	# Calling main() function
	main()
