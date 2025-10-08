/**
 * User profile management system with mixed quality patterns
 * Demonstrates both good and poor coding practices
 */

class UserProfileManager {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.cache = new Map();
        this.requestQueue = [];
    }

    /**
     * Retrieves user profile with caching support and error handling
     * @param {string} userId - The user identifier (required)
     * @returns {Promise<Object>} User profile data
     * @throws {Error} If userId is invalid or request fails
     */
    async getUserProfile(userId) {
        if (!userId || typeof userId !== 'string') {
            throw new Error('Valid user ID string is required');
        }

        // Check cache first for performance
        if (this.cache.has(userId)) {
            return this.cache.get(userId);
        }

        try {
            const profile = await this.apiClient.get(`/users/${userId}`);
            
            // Cache the result with TTL
            this.cache.set(userId, profile);
            setTimeout(() => {
                this.cache.delete(userId);
            }, 300000); // 5 minutes TTL
            
            return profile;
        } catch (error) {
            console.error('Failed to fetch user profile:', error);
            throw new Error(`Profile fetch failed: ${error.message}`);
        }
    }

    // POOR QUALITY: Deep nesting, no documentation, unclear logic
    updateUserPreferences(userId, preferences) {
        if (userId) {
            if (preferences) {
                if (typeof preferences === 'object') {
                    if (preferences.theme) {
                        if (preferences.theme === 'dark' || preferences.theme === 'light') {
                            if (preferences.language) {
                                if (preferences.language.length === 2) {
                                    if (preferences.notifications) {
                                        if (preferences.notifications.email !== undefined) {
                                            if (preferences.notifications.push !== undefined) {
                                                if (preferences.privacy) {
                                                    if (preferences.privacy.shareData !== undefined) {
                                                        return this.apiClient.patch(`/users/${userId}/preferences`, preferences);
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        return null;
    }

    // POOR QUALITY: No error handling, unclear nested loops, no documentation
    processUserData(data) {
        let result = [];
        for (let i = 0; i < data.length; i++) {
            for (let j = 0; j < data[i].items.length; j++) {
                for (let k = 0; k < data[i].items[j].properties.length; k++) {
                    for (let l = 0; l < data[i].items[j].properties[k].values.length; l++) {
                        result.push(data[i].items[j].properties[k].values[l]);
                    }
                }
            }
        }
        return result;
    }

    // DUPLICATE CODE: Similar to getUserProfile but with slight differences
    async getUser(userId) {
        if (!userId) {
            throw new Error('User ID is required');
        }

        if (this.cache.has(userId)) {
            return this.cache.get(userId);
        }

        try {
            const user = await this.apiClient.get(`/users/${userId}`);
            this.cache.set(userId, user);
            return user;
        } catch (error) {
            console.error('Failed to fetch user:', error);
            throw error;
        }
    }

    // DUPLICATE CODE: Another similar method
    async fetchUserData(id) {
        if (!id) {
            throw new Error('ID is required');
        }

        if (this.cache.has(id)) {
            return this.cache.get(id);
        }

        try {
            const userData = await this.apiClient.get(`/users/${id}`);
            this.cache.set(id, userData);
            return userData;
        } catch (error) {
            console.error('Failed to fetch user data:', error);
            throw error;
        }
    }
}

// POOR QUALITY: No class, global functions, no error handling
function validateEmail(email) {
    if (email) {
        if (email.includes('@')) {
            if (email.includes('.')) {
                if (email.length > 5) {
                    if (email.indexOf('@') > 0) {
                        if (email.lastIndexOf('.') > email.indexOf('@')) {
                            return true;
                        }
                    }
                }
            }
        }
    }
    return false;
}
