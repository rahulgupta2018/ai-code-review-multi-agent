// 🔐 Authentication Domain Service - Application Service Implementation

import * as https from 'https';
import {
  OAuthServiceAdapter,
  UserServiceAdapter,
  // SessionServiceAdapter, // DISABLED: Session management commented out
  RBACServiceAdapter,
  // CacheServiceAdapter, // DISABLED: Cache layer commented out
  AuditServiceAdapter,
} from '../../infrastructure/adapters';
import type {
  OAuthTokenResponse,
  User,
  // Session, // DISABLED: Session management commented out
  UserRole,
  CreateUserRequest,
  // CreateSessionRequest, // DISABLED: Session management commented out
  AssignDefaultRoleRequest,
  FindUserByProviderRequest
} from '../../infrastructure/adapters';
import { JWTService, JWTPayload } from '../../infrastructure/services/JWTService';
import { OAuthTokenVerificationService } from '../../infrastructure/services/OAuthTokenVerificationService';

// Request/Response interfaces
export interface OAuthCallbackRequest {
  provider: 'google' | 'microsoft';
  code: string;
  state?: string;
}

export interface OAuthAuthenticationRequest {
  accessToken: string;
  refreshToken?: string;
  idToken?: string;
  provider: 'google' | 'microsoft';
}

export interface ProcessedOAuthCallbackRequest {
  provider: 'google' | 'microsoft';
  access_token: string;
  id_token?: string;
  refresh_token?: string;
  expires_in: string;
  user_id: string;
  email: string;
  name: string;
  picture?: string;
  state?: string;
  correlation_id: string;
  frontend_callback: string;
}

export interface AuthenticationResponse {
  user: User;
  session: any | null; // DISABLED: Session management - return null when disabled
  tokens: {
    accessToken: string;
    refreshToken: string;
    expiresAt: string;
  };
  roles: UserRole[];
}

export interface RefreshTokenRequest {
  refreshToken: string;
}

export interface VerifyTokenRequest {
  token: string;
}

export interface UserProfileResponse {
  user: User;
  roles: UserRole[];
  permissions: string[];
}

// User info extracted from OAuth ID token
interface UserInfoFromToken {
  email: string;
  firstName?: string;
  lastName?: string;
  profilePicture?: string;
  providerId: string;
  emailVerified?: boolean;
}

/**
 * Authentication Application Service
 * Orchestrates authentication flows by calling System APIs
 */
export class AuthenticationAppService {
  private readonly oauthVerificationService: OAuthTokenVerificationService;

  constructor(
    private readonly oauthAdapter: OAuthServiceAdapter,
    private readonly userAdapter: UserServiceAdapter,
    private readonly sessionAdapter: any | null, // Made optional for session management toggle - any type since SessionServiceAdapter not imported
    private readonly rbacAdapter: RBACServiceAdapter,
    private readonly cacheAdapter: any | null, // Made optional for cache toggle - any type since CacheServiceAdapter not imported
    private readonly auditAdapter: AuditServiceAdapter,
    private readonly jwtService: JWTService
  ) {
    // Initialize OAuth token verification service
    this.oauthVerificationService = new OAuthTokenVerificationService({
      debug: (message: string, metadata?: any) => console.debug(`[OAuth] ${message}`, metadata),
      info: (message: string, metadata?: any) => console.info(`[OAuth] ${message}`, metadata),
      warn: (message: string, metadata?: any) => console.warn(`[OAuth] ${message}`, metadata),
      error: (message: string, metadata?: any, error?: Error) => console.error(`[OAuth] ${message}`, metadata, error)
    });
  }

  /**
   * Generate Google OAuth authorization URL via OAuth Service
   * Calls OAuth service through API Gateway to get proper authorization URL
   */
  async getGoogleAuthorizationUrl(state?: string): Promise<string> {
    try {
      // Generate secure state parameter if not provided
      const oauthState = state || this.generateOAuthState();
      
      // Fixed redirect URI as per OAuth Integration Guide
      const redirectUri = 'https://oauth.ai-study-assistant.dev:8443/api/v1/oauth/google/callback';
      
      // Cache the state for CSRF validation (10 minutes TTL) - skip if cache disabled
      if (this.cacheAdapter) {
        this.cacheAdapter.cacheOAuthState(oauthState, {
          provider: 'google',
          createdAt: new Date().toISOString(),
          redirectUri: redirectUri
        }, 600);
      }

      // Call OAuth service via API Gateway to get authorization URL
      const apiGatewayBaseUrl = process.env.API_GATEWAY_BASE_URL || 'https://ai-study-assistant-apigateway-api-gateway-1:9002';
      const initiateUrl = `${apiGatewayBaseUrl}/api/v1/oauth/google/initiate`;
      
      // Configure fetch options for development environment with self-signed certificates
      const fetchOptions: RequestInit = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          redirect_uri: redirectUri,
          state: oauthState
        })
      };

      // In development, we need to handle self-signed certificates
      if (process.env.NODE_ENV !== 'production') {
        // Use imported https module for custom agent
        (fetchOptions as any).agent = new https.Agent({
          rejectUnauthorized: false
        });
      }

      const response = await fetch(initiateUrl, fetchOptions);

      if (!response.ok) {
        throw new Error(`OAuth initiation failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json() as {
        success: boolean;
        message?: string;
        data?: {
          authorization_url: string;
          state: string;
          provider: string;
        };
      };
      
      if (!result.success) {
        throw new Error(`OAuth initiation failed: ${result.message || 'Unknown error'}`);
      }

      return result.data!.authorization_url;
    } catch (error) {
      throw new Error(`Google OAuth redirect URI not configured: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Generate Microsoft OAuth authorization URL via OAuth Service
   * Calls OAuth service through API Gateway to get proper authorization URL
   */
  async getMicrosoftAuthorizationUrl(state?: string): Promise<string> {
    try {
      // Generate secure state parameter if not provided
      const oauthState = state || this.generateOAuthState();
      
      // Fixed redirect URI as per OAuth Integration Guide (Microsoft will be added later)
      const redirectUri = 'https://oauth.ai-study-assistant.dev:8443/api/v1/oauth/microsoft/callback';
      
      // Cache the state for CSRF validation (10 minutes TTL) - skip if cache disabled
      if (this.cacheAdapter) {
        this.cacheAdapter.cacheOAuthState(oauthState, {
          provider: 'microsoft',
          createdAt: new Date().toISOString(),
          redirectUri: redirectUri
        }, 600);
      }

      // Call OAuth service via API Gateway to get authorization URL
      const apiGatewayBaseUrl = process.env.API_GATEWAY_BASE_URL || 'https://ai-study-assistant-apigateway-api-gateway-1:9002';
      const initiateUrl = `${apiGatewayBaseUrl}/api/v1/oauth/microsoft/initiate`;
      
      // Configure fetch options for development environment with self-signed certificates
      const fetchOptions: RequestInit = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          redirect_uri: redirectUri,
          state: oauthState
        })
      };

      // In development, we need to handle self-signed certificates
      if (process.env.NODE_ENV !== 'production') {
        // Use imported https module for custom agent
        (fetchOptions as any).agent = new https.Agent({
          rejectUnauthorized: false
        });
      }

      const response = await fetch(initiateUrl, fetchOptions);

      if (!response.ok) {
        throw new Error(`OAuth initiation failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json() as {
        success: boolean;
        message?: string;
        data?: {
          authorization_url: string;
          state: string;
          provider: string;
        };
      };
      
      if (!result.success) {
        throw new Error(`OAuth initiation failed: ${result.message || 'Unknown error'}`);
      }

      return result.data!.authorization_url;
    } catch (error) {
      throw new Error(`Microsoft OAuth redirect URI not configured: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Process OAuth callback and complete authentication flow
   * This orchestrates calls to all System APIs with caching optimization
   */
  async processOAuthCallback(request: OAuthCallbackRequest, ipAddress?: string, userAgent?: string): Promise<AuthenticationResponse> {
    try {
      console.log(`[AuthenticationAppService] Processing OAuth callback for provider: ${request.provider}`);

      // Generate cache-friendly state for OAuth flow tracking
      const oAuthState = request.state;
      if (oAuthState && this.cacheAdapter) {
        // Validate OAuth state from cache for CSRF protection (only if cache enabled)
        const stateData = await this.cacheAdapter.consumeOAuthState(oAuthState);
        if (!stateData) {
          throw new Error('Invalid or expired OAuth state');
        }
      } else if (oAuthState) {
        console.log(`[AuthenticationAppService] OAuth state validation skipped (cache disabled) for provider: ${request.provider}`);
      }

      // Step 1: Exchange authorization code for tokens via OAuth Service
      const tokenResponse = await this.oauthAdapter.authenticateWithOAuth({
        provider: request.provider,
        code: request.code,
        redirectUri: request.provider === 'google' 
          ? process.env.GOOGLE_REDIRECT_URI! 
          : process.env.MICROSOFT_REDIRECT_URI!,
        clientId: request.provider === 'google' 
          ? process.env.GOOGLE_CLIENT_ID 
          : process.env.MICROSOFT_CLIENT_ID,
        state: request.state
      });

      // Step 2: Extract user info from OAuth service response (already verified by OAuth service)
      // The OAuth service has already verified the provider tokens and returned user profile
      const userInfo: UserInfoFromToken = {
        email: tokenResponse.user_profile?.email || '',
        firstName: tokenResponse.user_profile?.given_name,
        lastName: tokenResponse.user_profile?.family_name,
        profilePicture: tokenResponse.user_profile?.picture,
        providerId: tokenResponse.user_profile?.sub || '',
        emailVerified: tokenResponse.user_profile?.email_verified || false
      };

      if (!userInfo.email || !userInfo.providerId) {
        throw new Error('Invalid user profile data from OAuth service');
      }

      console.log(`[AuthenticationAppService] Using user profile from OAuth service for ${userInfo.email}`);

      // Step 3: Check cache for user data first (skip if cache disabled)
      let user: User | null = null;
      if (this.cacheAdapter) {
        user = await this.cacheAdapter.getUserProfile(`provider_${request.provider}_${userInfo.providerId}`);
      }
      
      if (!user) {
        // Cache miss or cache disabled - get user from User Service
        user = await this.userAdapter.findUserByProvider({
          provider: request.provider,
          providerId: userInfo.providerId
        });

        if (user && this.cacheAdapter) {
          // Cache the user profile for faster lookups (only if cache enabled)
          await this.cacheAdapter.cacheUserProfile(user.id, user, 1800); // 30 minutes
          await this.cacheAdapter.set(
            `provider_${request.provider}_${userInfo.providerId}`,
            user,
            1800
          );
        }
      }

      if (!user) {
        // Create new user
        user = await this.userAdapter.createUser({
          email: userInfo.email,
          name: `${userInfo.firstName || ''} ${userInfo.lastName || ''}`.trim() || userInfo.email.split('@')[0], // Combine names or use email prefix
          avatar: userInfo.profilePicture,
          oauth_id: userInfo.providerId,
          oauth_provider: request.provider
        });

        // Cache new user data (only if cache enabled)
        if (this.cacheAdapter) {
          await this.cacheAdapter.cacheUserProfile(user.id, user, 1800);
          await this.cacheAdapter.set(
            `provider_${request.provider}_${userInfo.providerId}`,
            user,
            1800
          );
        }

        // Assign default role for new user
        const defaultRole = await this.rbacAdapter.assignDefaultRole({
          userId: user.id,
          userEmail: user.email
        });

        // Cache user roles immediately (only if cache enabled)
        if (this.cacheAdapter) {
          await this.cacheAdapter.cacheUserRoles(user.id, [defaultRole], 1800);
        }

        // Log registration event
        await this.auditAdapter.logRegistration(
          user.id,
          request.provider,
          ipAddress,
          userAgent
        );
      }

      // Step 4: Create session via Session Service (only if session management enabled)
      let session: any = null;
      if (this.sessionAdapter) {
        session = await this.sessionAdapter.createSession({
          user_id: user.id,  // Changed from userId to user_id
          accessToken: tokenResponse.accessToken,
          refreshToken: tokenResponse.refreshToken,
          expiresAt: this.calculateExpiryDate(tokenResponse.expiresIn),
          userAgent,
          ipAddress,
          device_info: {
            device_id: require('crypto').randomUUID(),
            device_type: 'web',
            user_agent: userAgent || 'unknown',
            platform: 'web'
          },
          location: {
            ip_address: ipAddress || 'unknown',
            country: 'unknown'
          }
        });

        // Cache session data for quick access (only if cache enabled)
        if (this.cacheAdapter) {
          await this.cacheAdapter.cacheUserSession(user.id, session, 3600); // 1 hour
        }
      }

      // Cache OAuth tokens for token refresh operations (only if cache enabled)
      if (this.cacheAdapter) {
        await this.cacheAdapter.cacheOAuthTokens(user.id, {
          accessToken: tokenResponse.accessToken,
          refreshToken: tokenResponse.refreshToken,
          expiresAt: this.calculateExpiryDate(tokenResponse.expiresIn)
        }, tokenResponse.expiresIn);
      }

      // Step 5: Get user roles (check cache first if enabled)
      let roles: UserRole[] | null = null;
      if (this.cacheAdapter) {
        roles = await this.cacheAdapter.getUserRoles(user.id);
      }
      if (!roles) {
        // Cache miss or cache disabled - get role assignments from RBAC Service
        roles = await this.rbacAdapter.getUserRoleAssignments(user.id);
        // Cache roles for faster permission checks (only if cache enabled)
        if (this.cacheAdapter) {
          await this.cacheAdapter.cacheUserRoles(user.id, roles, 1800); // 30 minutes
        }
      }

      // Step 6: Log login event (with or without session ID)
      await this.auditAdapter.logLogin(
        user.id,
        session?.id || '',
        ipAddress,
        userAgent
      );

      // Step 6: Generate JWT tokens for the authenticated user (CRITICAL FIX)
      console.log(`[AuthenticationAppService] User object before JWT generation:`, JSON.stringify({
        id: user.id,
        email: user.email,
        hasId: !!user.id,
        userKeys: Object.keys(user),
        userType: typeof user.id
      }, null, 2));

      if (!user.id) {
        throw new Error(`User ID is missing. User object: ${JSON.stringify(user, null, 2)}`);
      }

      const jwtPayload: JWTPayload = {
        userId: user.id,
        email: user.email,
        isVerified: true // OAuth providers verify emails
      };

      const tokenPair = this.jwtService.generateTokenPair(jwtPayload);
      
      // Cache JWT tokens (only if cache enabled)
      if (this.cacheAdapter) {
        await this.cacheAdapter.cacheToken(tokenPair.accessToken, {
          userId: user.id,
          expiresAt: tokenPair.expiresAt.toISOString(),
          scopes: ['read', 'write']
        }, 3600); // 1 hour

        await this.cacheAdapter.cacheToken(tokenPair.refreshToken, {
          userId: user.id,
          expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days
          scopes: ['read', 'write']
        }, 7 * 24 * 60 * 60); // 7 days
      }

      console.log(`[AuthenticationAppService] OAuth authentication completed for user: ${user.id} with JWT tokens`);

      return {
        user,
        session,
        tokens: {
          accessToken: tokenPair.accessToken,    // ✅ OUR JWT TOKEN (not Google's)
          refreshToken: tokenPair.refreshToken,  // ✅ OUR JWT TOKEN (not Google's)
          expiresAt: tokenPair.expiresAt.toISOString()
        },
        roles: roles || []
      };

    } catch (error) {
      console.error(`[AuthenticationAppService] OAuth callback processing failed:`, error);
      
      // Log failure event
      await this.auditAdapter.logOAuthFailure(
        request.provider,
        error instanceof Error ? error.message : 'Unknown error',
        ipAddress,
        userAgent
      );

      throw new Error(`OAuth authentication failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Handle processed OAuth callback with pre-exchanged tokens from OAuth Service
   */
  async processProcessedOAuthCallback(request: ProcessedOAuthCallbackRequest): Promise<AuthenticationResponse> {
    try {
      console.log(`[AuthenticationAppService] Processing processed OAuth callback for provider: ${request.provider}`);

      // Create user info from the processed OAuth data
      const userInfo = {
        providerId: request.user_id,
        email: request.email,
        firstName: request.name.split(' ')[0] || '',
        lastName: request.name.split(' ').slice(1).join(' ') || '',
        profilePicture: request.picture || undefined
      };

      // Check if user exists by provider
      let user = await this.userAdapter.findUserByProvider({
        provider: request.provider,
        providerId: userInfo.providerId
      });

      if (user && this.cacheAdapter) {
        // Cache the user profile for faster lookups (only if cache enabled)
        await this.cacheAdapter.cacheUserProfile(user.id, user, 1800); // 30 minutes
        await this.cacheAdapter.set(
          `provider_${request.provider}_${userInfo.providerId}`,
          user,
          1800
        );
      }

      if (!user) {
        // Create new user
        user = await this.userAdapter.createUser({
          email: userInfo.email,
          name: `${userInfo.firstName} ${userInfo.lastName}`.trim() || userInfo.email.split('@')[0],
          avatar: userInfo.profilePicture,
          oauth_id: userInfo.providerId,
          oauth_provider: request.provider
        });

        console.log(`[AuthenticationAppService] Created new user for ${request.provider} OAuth: ${user.id}`);
      } else {
        // Update existing user's profile picture if provided
        if (userInfo.profilePicture) {
          await this.userAdapter.updateUser(user.id, {
            profilePicture: userInfo.profilePicture
          });
        }

        console.log(`[AuthenticationAppService] Updated existing user for ${request.provider} OAuth: ${user.id}`);
      }

      // Generate JWT tokens for the authenticated user
      const jwtPayload: JWTPayload = {
        userId: user.id,
        email: user.email,
        isVerified: true // OAuth providers verify emails
      };

      const tokenPair = this.jwtService.generateTokenPair(jwtPayload);
      const expiresAt = new Date(Date.now() + 60 * 60 * 1000).toISOString(); // 1 hour

      // Cache tokens (only if cache enabled)
      if (this.cacheAdapter) {
        await this.cacheAdapter.cacheToken(tokenPair.accessToken, {
          userId: user.id,
          expiresAt,
          scopes: ['read', 'write']
        }, 3600); // 1 hour

        await this.cacheAdapter.cacheToken(tokenPair.refreshToken, {
          userId: user.id,
          expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days
          scopes: ['read', 'write']
        }, 7 * 24 * 60 * 60); // 7 days
      }

      // Get user roles and convert to UserRole format
      const rolesData = await this.rbacAdapter.getUserRoles(user.id);
      const roles = rolesData.map(role => ({
        id: role.id,
        userId: user.id,
        roleId: role.id,
        roleName: role.name,
        assignedAt: new Date().toISOString(),
        assignedBy: 'system',
        isActive: true
      }));

      // Log successful OAuth authentication
      await this.auditAdapter.logLogin(
        user.id,
        'oauth-session', // OAuth doesn't use traditional sessions
        undefined, // ipAddress not available from processed callback
        undefined, // userAgent not available from processed callback
        request.correlation_id
      );

      console.log(`[AuthenticationAppService] Successfully processed OAuth callback for user: ${user.id}`);

      return {
        user,
        session: null, // DISABLED: Session management - return null when disabled
        tokens: {
          accessToken: tokenPair.accessToken,
          refreshToken: tokenPair.refreshToken,
          expiresAt
        },
        roles
      };
    } catch (error) {
      console.error(`[AuthenticationAppService] Processed OAuth callback failed:`, error);

      // Log failure event
      await this.auditAdapter.logOAuthFailure(
        request.provider,
        error instanceof Error ? error.message : 'Unknown error',
        undefined, // ipAddress not available from processed callback
        undefined, // userAgent not available from processed callback
        request.correlation_id
      );

      throw new Error(`Processed OAuth authentication failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Handle OAuth registration with existing tokens
   */
  async registerWithOAuth(request: OAuthAuthenticationRequest, ipAddress?: string, userAgent?: string): Promise<AuthenticationResponse> {
    try {
      console.log(`[AuthenticationAppService] Processing OAuth registration for provider: ${request.provider}`);

      // Extract user info from tokens with cryptographic verification
      const userInfo = await this.extractUserInfoFromToken(request.idToken, request.provider);

      // Check if user already exists
      const existingUser = await this.userAdapter.findUserByProvider({
        provider: request.provider,
        providerId: userInfo.providerId
      });

      if (existingUser) {
        throw new Error('User already exists with this provider');
      }

      // Create new user
      const user = await this.userAdapter.createUser({
        email: userInfo.email,
        name: `${userInfo.firstName || ''} ${userInfo.lastName || ''}`.trim() || userInfo.email.split('@')[0], // Combine names or use email prefix
        avatar: userInfo.profilePicture,
        oauth_id: userInfo.providerId,
        oauth_provider: request.provider
      });

      // Assign default role
      await this.rbacAdapter.assignDefaultRole({
        userId: user.id,
        userEmail: user.email
      });

      // Create session (only if session management enabled)
      let session: any = null;
      if (this.sessionAdapter) {
        session = await this.sessionAdapter.createSession({
          user_id: user.id,  // Changed from userId to user_id
          accessToken: request.accessToken,
          refreshToken: request.refreshToken || '',
          expiresAt: new Date(Date.now() + 3600000).toISOString(), // 1 hour default
          userAgent,
          ipAddress,
          device_info: {
            device_id: require('crypto').randomUUID(),
            device_type: 'web',
            user_agent: userAgent || 'unknown',
            platform: 'web'
          },
          location: {
            ip_address: ipAddress || 'unknown',
            country: 'unknown'
          }
        });
      }

      // Get user roles
      const roles = await this.rbacAdapter.getUserRoleAssignments(user.id);

      // Log registration
      await this.auditAdapter.logRegistration(user.id, request.provider, ipAddress, userAgent);

      return {
        user,
        session,
        tokens: {
          accessToken: request.accessToken,
          refreshToken: request.refreshToken || '',
          expiresAt: session?.expiresAt || new Date(Date.now() + 3600000).toISOString() // 1 hour default when session disabled
        },
        roles
      };

    } catch (error) {
      console.error(`[AuthenticationAppService] OAuth registration failed:`, error);
      throw new Error(`OAuth registration failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Handle OAuth login with existing tokens
   */
  async loginWithOAuth(request: OAuthAuthenticationRequest, ipAddress?: string, userAgent?: string): Promise<AuthenticationResponse> {
    try {
      console.log(`[AuthenticationAppService] Processing OAuth login for provider: ${request.provider}`);

      // Extract user info from tokens with cryptographic verification
      const userInfo = await this.extractUserInfoFromToken(request.idToken, request.provider);

      // Find existing user
      const user = await this.userAdapter.findUserByProvider({
        provider: request.provider,
        providerId: userInfo.providerId
      });

      if (!user) {
        throw new Error('User not found. Please register first.');
      }

      // Update user info if needed
      await this.userAdapter.updateUser(user.id, {
        firstName: userInfo.firstName,
        lastName: userInfo.lastName,
        profilePicture: userInfo.profilePicture
      });

      // Create new session (only if session management enabled)
      let session: any = null;
      if (this.sessionAdapter) {
        session = await this.sessionAdapter.createSession({
          user_id: user.id,  // Changed from userId to user_id
          accessToken: request.accessToken,
          refreshToken: request.refreshToken || '',
          expiresAt: new Date(Date.now() + 3600000).toISOString(), // 1 hour default
          userAgent,
          ipAddress,
          device_info: {
            device_id: require('crypto').randomUUID(),
            device_type: 'web',
            user_agent: userAgent || 'unknown',
            platform: 'web'
          },
          location: {
            ip_address: ipAddress || 'unknown',
            country: 'unknown'
          }
        });
      }

      // Get user roles
      const roles = await this.rbacAdapter.getUserRoleAssignments(user.id);

      // Log login (with or without session ID)
      await this.auditAdapter.logLogin(user.id, session?.id || '', ipAddress, userAgent);

      return {
        user,
        session,
        tokens: {
          accessToken: request.accessToken,
          refreshToken: request.refreshToken || '',
          expiresAt: session?.expiresAt || new Date(Date.now() + 3600000).toISOString()
        },
        roles
      };

    } catch (error) {
      console.error(`[AuthenticationAppService] OAuth login failed:`, error);
      throw new Error(`OAuth login failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Refresh access token via External OAuth Service
   */
  async refreshToken(request: RefreshTokenRequest, correlationId?: string): Promise<{ accessToken: string; refreshToken: string; expiresAt: string }> {
    try {
      console.log(`[AuthenticationAppService] Processing token refresh via external OAuth service`);

      // Refresh token via External OAuth Service
      const tokenResponse = await this.oauthAdapter.refreshToken(request);

      // DISABLED: Session management - no session lookup or update needed
      // If session management was enabled, we would update the session here

      // Log token refresh (without session ID when session management is disabled)
      // Note: We don't have userId from refresh token directly, so we log without it
      await this.auditAdapter.logTokenRefresh('', '', correlationId);

      return {
        accessToken: tokenResponse.accessToken,
        refreshToken: tokenResponse.refreshToken,
        expiresAt: this.calculateExpiryDate(tokenResponse.expiresIn)
      };

    } catch (error) {
      console.error(`[AuthenticationAppService] Token refresh failed:`, error);
      throw new Error(`Token refresh failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Verify token validity via External OAuth Service
   */
  async verifyToken(request: VerifyTokenRequest): Promise<{ valid: boolean; userId?: string; scopes?: string[] }> {
    try {
      // Use external OAuth service to validate the token
      const validationResult = await this.oauthAdapter.validateToken({ token: request.token });
      
      return {
        valid: validationResult.valid,
        userId: validationResult.userId,
        scopes: validationResult.scopes || []
      };
    } catch (error) {
      console.error(`[AuthenticationAppService] Token verification failed:`, error);
      return { valid: false };
    }
  }

  /**
   * Logout user and end session with cache cleanup
   */
  async logout(sessionId: string, userId: string, ipAddress?: string, userAgent?: string): Promise<void> {
    try {
      // End session (only if session management enabled)
      if (this.sessionAdapter) {
        await this.sessionAdapter.endSession(sessionId);
      }

      // Clear all cached data for the user (only if cache enabled)
      if (this.cacheAdapter) {
        await this.cacheAdapter.invalidateUserCache(userId);
      }

      // Log logout
      await this.auditAdapter.logLogout(userId, sessionId, ipAddress, userAgent);

    } catch (error) {
      console.error(`[AuthenticationAppService] Logout failed:`, error);
      throw new Error(`Logout failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get user profile with roles and permissions (production-grade with caching)
   */
  async getUserProfile(userId: string): Promise<UserProfileResponse> {
    try {
      // Check cache for user profile (only if cache enabled)
      let user: User | null = null;
      if (this.cacheAdapter) {
        user = await this.cacheAdapter.getUserProfile(userId);
      }
      if (!user) {
        // Cache miss - get user from User Service
        user = await this.userAdapter.getUserById(userId);
        // Cache for 30 minutes - don't fail if caching fails (only if cache enabled)
        if (this.cacheAdapter) {
          try {
            await this.cacheAdapter.cacheUserProfile(userId, user, 1800);
          } catch (cacheError) {
            // Log cache error but don't fail the request
            console.warn('[AuthenticationAppService] Failed to cache user profile:', cacheError);
          }
        }
      }

      // Check cache for user roles (only if cache enabled)
      let cachedRoles: UserRole[] | null = null;
      if (this.cacheAdapter) {
        cachedRoles = await this.cacheAdapter.getUserRoles(userId);
      }
      let roles: UserRole[];
      
      if (!cachedRoles) {
        // Cache miss or cache disabled - get role assignments from RBAC Service
        roles = await this.rbacAdapter.getUserRoleAssignments(userId);
        // Cache for 30 minutes - don't fail if caching fails (only if cache enabled)
        if (this.cacheAdapter) {
          try {
            await this.cacheAdapter.cacheUserRoles(userId, roles, 1800);
          } catch (cacheError) {
            // Log cache error but don't fail the request
            console.warn('[AuthenticationAppService] Failed to cache user roles:', cacheError);
          }
        }
      } else {
        roles = cachedRoles;
      }

      // Get user permissions (these change less frequently, so cache longer)
      const cacheKey = `user_permissions:${userId}`;
      let permissionStrings: string[] = [];
      
      // Check cache for permissions (only if cache enabled)
      let cachedPermissions: any = null;
      if (this.cacheAdapter) {
        cachedPermissions = await this.cacheAdapter.get(cacheKey);
      }
      
      if (cachedPermissions?.value) {
        permissionStrings = cachedPermissions.value;
      } else {
        // Cache miss or cache disabled - get permissions from RBAC Service
        const permissionObjects = await this.rbacAdapter.getUserPermissions(userId);
        permissionStrings = permissionObjects.map(p => `${p.resource}:${p.action}`);
        
        // Cache permissions for 1 hour (only if cache enabled)
        if (this.cacheAdapter) {
          await this.cacheAdapter.set(
            cacheKey,
            permissionStrings,
            3600
          );
        }
      }

      return {
        user,
        roles,
        permissions: permissionStrings
      };

    } catch (error) {
      console.error(`[AuthenticationAppService] Get user profile failed:`, error);
      throw new Error(`Get user profile failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

    /**
   * 🔒 SECURE: Extract and cryptographically verify user info from OAuth ID token
   * This method validates the token signature with OAuth provider public keys
   */
  private async extractUserInfoFromToken(
    idToken?: string, 
    provider?: 'google' | 'microsoft'
  ): Promise<UserInfoFromToken> {
    if (!idToken) {
      throw new Error('ID token is required for OAuth authentication');
    }

    if (!provider) {
      throw new Error('OAuth provider is required for token verification');
    }

    try {
      console.log(`[AuthenticationAppService] Verifying OAuth ID token for provider: ${provider}`);

      // Check if OAuth provider is properly configured
      const providerStatus = this.oauthVerificationService.getProviderStatus();
      const isConfigured = provider === 'google' ? providerStatus.google : providerStatus.microsoft;

      if (!isConfigured) {
        console.warn(`[AuthenticationAppService] OAuth provider ${provider} not configured, using testing verification`);
        
        // For development/testing only - validates structure but not signature
        if (process.env.NODE_ENV !== 'production') {
          const testResult = this.oauthVerificationService.verifyTokenForTesting(idToken, provider);
          if (!testResult.valid) {
            throw new Error(`Token verification failed: ${testResult.error}`);
          }
          return testResult.userInfo!;
        } else {
          throw new Error(`OAuth provider ${provider} not configured for production use`);
        }
      }

      // 🔒 SECURE: Cryptographically verify token with provider public keys
      const verificationResult = await this.oauthVerificationService.verifyOAuthToken(idToken, provider);
      
      if (!verificationResult.valid) {
        throw new Error(`OAuth token verification failed: ${verificationResult.error}`);
      }

      if (!verificationResult.userInfo) {
        throw new Error('No user information found in verified token');
      }

      console.log(`[AuthenticationAppService] OAuth token verified successfully for ${verificationResult.userInfo.email}`);
      return verificationResult.userInfo;

    } catch (error) {
      console.error('[AuthenticationAppService] OAuth token verification failed:', error);
      throw new Error(`OAuth authentication failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Helper method to calculate expiry date from seconds
   */
  private calculateExpiryDate(expiresIn: number): string {
    return new Date(Date.now() + (expiresIn * 1000)).toISOString();
  }

  /**
   * Generate secure OAuth state parameter
   */
  private generateOAuthState(): string {
    return require('crypto').randomBytes(32).toString('hex');
  }

  // =============================================================================
  // Integration Proxy Methods for Sidecar Services
  // =============================================================================

  /**
   * Get user roles (proxy to RBAC service)
   */
  async getUserRolesProxy(userId: string): Promise<any> {
    return this.rbacAdapter.getUserRoles(userId);
  }

  /**
   * Check user permission (proxy to RBAC service)
   */
  async checkPermissionProxy(userId: string, resource: string, action: string): Promise<boolean> {
    return this.rbacAdapter.hasPermission(userId, resource, action);
  }

  /**
   * Create session (proxy to session service)
   */
  async createSessionProxy(userId: string, ttl?: number): Promise<any> {
    // Generate proper JWT tokens for the session
    const expiresIn = ttl || 3600; // Default 1 hour
    
    // For proxy session creation, we need to get user email to create proper JWT
    // First try to get from cache (if enabled), then from user service
    let user: User | null = null;
    if (this.cacheAdapter) {
      user = await this.cacheAdapter.getUserProfile(userId);
    }
    if (!user) {
      user = await this.userAdapter.getUserById(userId);
    }
    
    const tokenPair = this.jwtService.generateTokenPair({ 
      userId,
      email: user.email,
      isVerified: true // Assume verified for proxy sessions
    });
    
    // DISABLED: Session management - return mock session data when disabled
    if (!this.sessionAdapter) {
      return {
        id: require('crypto').randomUUID(),
        user_id: userId,
        accessToken: tokenPair.accessToken,
        refreshToken: tokenPair.refreshToken,
        expiresAt: this.calculateExpiryDate(expiresIn),
        status: 'active',
        created_at: new Date().toISOString(),
        last_activity: new Date().toISOString()
      };
    }
    
    return this.sessionAdapter.createSession({
      user_id: userId,  // Changed from userId to user_id
      accessToken: tokenPair.accessToken,
      refreshToken: tokenPair.refreshToken,
      expiresAt: this.calculateExpiryDate(expiresIn),
      device_info: {
        device_id: require('crypto').randomUUID(),
        device_type: 'api',
        user_agent: 'proxy-session',
        platform: 'api'
      },
      location: {
        ip_address: 'internal',
        country: 'unknown'
      }
    });
  }

  /**
   * Get session (proxy to session service)
   */
  async getSessionProxy(sessionId: string): Promise<any> {
    // DISABLED: Session management - return null when disabled
    if (!this.sessionAdapter) {
      return null;
    }
    return this.sessionAdapter.getSessionById(sessionId);
  }

  /**
   * Create audit event (proxy to audit service)
   */
  async createAuditEventProxy(userId: string, action: string, resource: string, metadata?: any): Promise<any> {
    return this.auditAdapter.logEvent({
      eventType: 'USER_ACTION',
      severity: 'LOW',
      serviceId: 'authentication-service',
      resourceId: resource,
      action,
      description: `User ${userId} performed ${action} on ${resource}`,
      userId,
      metadata: {
        additional: metadata
      }
    });
  }

  /**
   * Get audit events (proxy to audit service)
   */
  async getAuditEventsProxy(userId?: string, limit?: number): Promise<any> {
    if (userId) {
      return this.auditAdapter.getUserEvents(userId, limit ? { limit } : undefined);
    } else {
      return this.auditAdapter.getEvents({ limit });
    }
  }

  /**
   * Set cache value (proxy to cache service)
   */
  async setCacheValueProxy(key: string, value: any, ttl?: number): Promise<any> {
    if (!this.cacheAdapter) {
      console.warn('[AuthenticationAppService] Cache disabled - setCacheValueProxy operation skipped');
      return { success: false, reason: 'Cache disabled' };
    }
    return this.cacheAdapter.set(
      key,
      value,
      ttl || 3600
    );
  }

  /**
   * Get cache value (proxy to cache service)
   */
  async getCacheValueProxy(key: string): Promise<any> {
    if (!this.cacheAdapter) {
      console.warn('[AuthenticationAppService] Cache disabled - getCacheValueProxy operation skipped');
      return null;
    }
    const result = await this.cacheAdapter.get(key);
    return result ? result.value : null;
  }
}
