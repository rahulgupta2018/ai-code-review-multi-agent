package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"
)

// Global variables - not recommended in Go
var globalCounter int
var sharedConfig map[string]interface{}

// User represents a user entity with validation issues
type User struct {
	ID       int    `json:"id"`
	Name     string `json:"name"`
	Email    string `json:"email"`
	Age      int    `json:"age"`
	IsActive bool   `json:"is_active"`
}

// UserService handles user operations with several code quality issues
type UserService struct {
	users []User
	errors []string
}

// ProcessUsers has high complexity and multiple responsibilities
func (us *UserService) ProcessUsers(users []User, includeInactive bool, validateEmail bool, formatOutput bool) ([]User, error) {
	var processedUsers []User
	
	// Deeply nested logic and complex conditions
	for i := 0; i < len(users); i++ {
		if users[i].ID > 0 {
			if len(users[i].Name) > 0 {
				if users[i].Age >= 0 && users[i].Age <= 150 {
					if includeInactive || users[i].IsActive {
						if validateEmail {
							if isValidEmail(users[i].Email) {
								processedUser := User{
									ID:       users[i].ID,
									Name:     strings.TrimSpace(users[i].Name),
									Email:    strings.ToLower(users[i].Email),
									Age:      users[i].Age,
									IsActive: users[i].IsActive,
								}
								
								if formatOutput {
									processedUser.Name = strings.Title(processedUser.Name)
								}
								
								processedUsers = append(processedUsers, processedUser)
							} else {
								us.errors = append(us.errors, fmt.Sprintf("Invalid email for user %d: %s", users[i].ID, users[i].Email))
							}
						} else {
							processedUser := User{
								ID:       users[i].ID,
								Name:     strings.TrimSpace(users[i].Name),
								Email:    users[i].Email,
								Age:      users[i].Age,
								IsActive: users[i].IsActive,
							}
							
							if formatOutput {
								processedUser.Name = strings.Title(processedUser.Name)
							}
							
							processedUsers = append(processedUsers, processedUser)
						}
					}
				} else {
					us.errors = append(us.errors, fmt.Sprintf("Invalid age for user %d: %d", users[i].ID, users[i].Age))
				}
			} else {
				us.errors = append(us.errors, fmt.Sprintf("Empty name for user %d", users[i].ID))
			}
		} else {
			us.errors = append(us.errors, fmt.Sprintf("Invalid ID for user: %d", users[i].ID))
		}
	}
	
	if len(us.errors) > 0 {
		return processedUsers, fmt.Errorf("processing completed with %d errors", len(us.errors))
	}
	
	return processedUsers, nil
}

// ValidateUsers - duplicate validation logic (code duplication)
func (us *UserService) ValidateUsers(users []User) []User {
	var validUsers []User
	
	for i := 0; i < len(users); i++ {
		if users[i].ID > 0 {
			if len(users[i].Name) > 0 {
				if users[i].Age >= 0 && users[i].Age <= 150 {
					validUsers = append(validUsers, users[i])
				}
			}
		}
	}
	
	return validUsers
}

// Long line that exceeds reasonable character limits and should be broken down for better readability and maintainability
func CreateComplexUserReportWithManyParametersAndLongName(userID int, userName string, userEmail string, userAge int, userAddress string, userPhone string, includePersonalInfo bool, includeContactInfo bool, formatAsJSON bool, formatAsXML bool, outputToFile bool, filePath string) string {
	// Function with too many parameters and long name
	report := make(map[string]interface{})
	report["id"] = userID
	report["name"] = userName
	
	if includePersonalInfo {
		report["age"] = userAge
	}
	
	if includeContactInfo {
		report["email"] = userEmail
		report["address"] = userAddress
		report["phone"] = userPhone
	}
	
	var output string
	if formatAsJSON {
		jsonData, _ := json.MarshalIndent(report, "", "  ")
		output = string(jsonData)
	} else if formatAsXML {
		output = convertToXML(report)
	} else {
		output = fmt.Sprintf("%+v", report)
	}
	
	if outputToFile && filePath != "" {
		ioutil.WriteFile(filePath, []byte(output), 0644)
	}
	
	return output
}

// Functions without proper error handling
func FetchUserFromAPI(url string) *User {
	response, err := http.Get(url)
	if err != nil {
		fmt.Println("Error fetching user:", err)
		return nil
	}
	defer response.Body.Close()
	
	body, _ := ioutil.ReadAll(response.Body)
	
	var user User
	json.Unmarshal(body, &user)
	
	return &user
}

// Function without proper documentation
func calculateSomething(a, b, c int) int {
	return a*b + c
}

// Utility functions
func isValidEmail(email string) bool {
	return strings.Contains(email, "@") && strings.Contains(email, ".")
}

func convertToXML(data map[string]interface{}) string {
	xml := "<user>\n"
	for key, value := range data {
		xml += fmt.Sprintf("  <%s>%v</%s>\n", key, value, key)
	}
	xml += "</user>"
	return xml
}

// Dead code - unused function
func unusedFunction() {
	fmt.Println("This function is never called")
}

// Main function with too much logic (should be split)
func main() {
	// Initialize global variables
	globalCounter = 0
	sharedConfig = make(map[string]interface{})
	
	userService := &UserService{}
	
	// Sample data
	users := []User{
		{ID: 1, Name: "John Doe", Email: "john@example.com", Age: 30, IsActive: true},
		{ID: 2, Name: " Jane Smith ", Email: "jane@example.com", Age: 25, IsActive: false},
		{ID: 3, Name: "", Email: "invalid-email", Age: -5, IsActive: true},
		{ID: 0, Name: "Invalid User", Email: "test@test.com", Age: 35, IsActive: true},
	}
	
	// Process users with complex parameters
	processedUsers, err := userService.ProcessUsers(users, true, true, true)
	if err != nil {
		fmt.Printf("Processing errors: %v\n", err)
		fmt.Printf("Error details: %v\n", userService.errors)
	}
	
	fmt.Printf("Processed %d users\n", len(processedUsers))
	
	// Validate users using duplicate logic
	validUsers := userService.ValidateUsers(users)
	fmt.Printf("Valid users: %d\n", len(validUsers))
	
	// Create complex report
	report := CreateComplexUserReportWithManyParametersAndLongName(1, "Test User", "test@example.com", 30, "123 Main St", "555-1234", true, true, true, false, false, "")
	fmt.Println("Generated report:")
	fmt.Println(report)
	
	// Global counter usage
	globalCounter++
	fmt.Printf("Global counter: %d\n", globalCounter)
}