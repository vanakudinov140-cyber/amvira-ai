export type GigachatOAuthTokenResponse = {
  readonly access_token?: string;
  readonly expires_at?: number;
};

export type GigachatChatCompletionMessage = {
  readonly role: string;
  readonly content?: string;
};

export type GigachatChatCompletionChoice = {
  readonly message?: GigachatChatCompletionMessage;
  readonly finish_reason?: string;
};

export type GigachatChatCompletionResponse = {
  readonly choices?: readonly GigachatChatCompletionChoice[];
  readonly usage?: {
    readonly prompt_tokens?: number;
    readonly completion_tokens?: number;
    readonly total_tokens?: number;
  };
  readonly error?: {
    readonly message?: string;
    readonly code?: number;
  };
};
