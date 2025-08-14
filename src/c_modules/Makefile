# Makefile pour les modules C/C++ Bluetooth

CC = gcc
CXX = g++
CFLAGS = -Wall -Wextra -O2 -fPIC
CXXFLAGS = -Wall -Wextra -O2 -fPIC -std=c++11
LDFLAGS = -lbluetooth -lpthread

# Répertoires
SRC_DIR = .
OBJ_DIR = obj
LIB_DIR = lib

# Fichiers sources
C_SOURCES = $(wildcard $(SRC_DIR)/*.c)
CXX_SOURCES = $(wildcard $(SRC_DIR)/*.cpp)
SOURCES = $(C_SOURCES) $(CXX_SOURCES)

# Fichiers objets
C_OBJECTS = $(C_SOURCES:$(SRC_DIR)/%.c=$(OBJ_DIR)/%.o)
CXX_OBJECTS = $(CXX_SOURCES:$(SRC_DIR)/%.cpp=$(OBJ_DIR)/%.o)
OBJECTS = $(C_OBJECTS) $(CXX_OBJECTS)

# Bibliothèques partagées
LIBS = $(LIB_DIR)/libbluetooth_attacks.so

# Cibles principales
all: directories $(LIBS)

directories:
	@mkdir -p $(OBJ_DIR) $(LIB_DIR)

# Compilation des objets C
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	@echo "Compiling $<..."
	@$(CC) $(CFLAGS) -c $< -o $@

# Compilation des objets C++
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp
	@echo "Compiling $<..."
	@$(CXX) $(CXXFLAGS) -c $< -o $@

# Création de la bibliothèque partagée
$(LIB_DIR)/libbluetooth_attacks.so: $(OBJECTS)
	@echo "Linking $@..."
	@$(CXX) -shared -o $@ $^ $(LDFLAGS)

# Installation
install: all
	@echo "Installing libraries..."
	@sudo cp $(LIBS) /usr/local/lib/
	@sudo ldconfig

# Nettoyage
clean:
	@echo "Cleaning..."
	@rm -rf $(OBJ_DIR) $(LIB_DIR)

# Tests
test: all
	@echo "Running tests..."
	@./test_bluetooth_attacks

# Dépendances
$(OBJ_DIR)/bluetooth_attacks.o: bluetooth_attacks.h
$(OBJ_DIR)/l2cap_attacks.o: l2cap_attacks.h
$(OBJ_DIR)/rfcomm_attacks.o: rfcomm_attacks.h
$(OBJ_DIR)/hci_attacks.o: hci_attacks.h

.PHONY: all clean install test directories
