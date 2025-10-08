# Code Analysis Report - AuthenticationAppService.ts
Generated: 2025-10-07 23:10:39
Agent: CodeAnalyzerAgent (Direct Tools Test)

## File Information
- **File**: /app/tests/input_files/AuthenticationAppService.ts
- **Size**: 40680 bytes
- **Lines**: 1145
- **Analysis Time**: 0.22s
- **Agent Tools**: 8
- **Test Method**: Direct tools invocation

## Summary
- **Total Findings**: 0
- **Tools Tested**: 2

## Tools Results
### Maintainability Scoring
- **Findings**: 0

### Maintainability Assessment
- **Findings**: 0
- **total_lines**: 1145
- **code_lines**: 996
- **comment_lines**: 100
- **comment_ratio**: 0.10
- **function_count**: 0
- **class_count**: 1
- **avg_lines_per_function**: 996.00

## No Issues Found

The code analyzer found no issues with this file.

## Code Preview (First 50 lines)
```typescript
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
```

