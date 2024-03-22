import { TrackableValue } from 'neuroglancer/trackable_value';

class BearerTokenManager {
    private static instance: BearerTokenManager;
    private _bearerToken: TrackableValue<string>;

    private constructor(initialValue: string = '') {
        // A simple string validator function
        const verifyString = (value: any): string => {
            if (typeof value !== 'string') {
                throw new Error('Value must be a string');
            }
            return value;
        };

        this._bearerToken = new TrackableValue<string>(initialValue, verifyString);
    }

    public static getInstance(): BearerTokenManager {
        if (!BearerTokenManager.instance) {
            BearerTokenManager.instance = new BearerTokenManager();
        }
        return BearerTokenManager.instance;
    }

    get bearerToken(): string {
        return this._bearerToken.value;
    }

    private set bearerToken(value: string) {
        this._bearerToken.value = value;
    }

    updateBearerTokenIfNeeded(newToken: string | undefined): void {
        if (newToken !== undefined) {
            this.bearerToken = newToken;
        }
    }
}

// Export a single instance
export const tokenManager = BearerTokenManager.getInstance();
