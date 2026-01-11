import requests
import logging
import time
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .config import settings

logger = logging.getLogger(__name__)

class APIError(Exception):
    pass

class AuthenticationError(APIError):
    pass

class RateLimitError(APIError):
    pass

class SoraClient:
    def __init__(self):
        self.base_url = settings.SORA_BASE_URL.rstrip('/')
        
        # Security: Headers are stored in session, avoid printing them directly
        self._headers = {
            "Authorization": f"Bearer {settings.SORA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Optimization: Use Session for Connection Pooling (Keep-Alive)
        self.session = requests.Session()
        self.session.headers.update(self._headers)
        
        # Optimization: Proxy configuration
        if settings.HTTP_PROXY:
            self.session.proxies.update({
                "http": settings.HTTP_PROXY, 
                "https": settings.HTTPS_PROXY or settings.HTTP_PROXY
            })
            
        # Optimization: Internal Retry Strategy for Connection Errors (TCP/DNS level)
        # This is different from the Tenacity retry which handles Logical API errors (500/429)
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=settings.MAX_CONCURRENT_TASKS, pool_maxsize=settings.MAX_CONCURRENT_TASKS)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        url = f"{self.base_url}{endpoint}"
        try:
            # Note: headers are already in session
            response = self.session.request(
                method, 
                url, 
                json=data, 
                timeout=settings.API_REQUEST_TIMEOUT_SECONDS
            )
            
            # Traceability: Log the Request ID from headers (common standard: x-request-id)
            req_id = response.headers.get("x-request-id", "unknown")
            if response.status_code >= 400:
                logger.warning(f"API Request Failed [ReqID: {req_id}] - Status: {response.status_code}")
            
            if response.status_code == 401:
                raise AuthenticationError(f"Invalid API Key [ReqID: {req_id}]")
            if response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded [ReqID: {req_id}]")
            
            response.raise_for_status()

            if response.status_code == 204:
                msg = f"Empty response (204) from API [ReqID: {req_id}]"
                logger.error(msg)
                raise APIError(msg)

            content_type = response.headers.get("Content-Type", "")
            if "application/json" not in content_type and "+json" not in content_type:
                body_preview = (response.text or "").strip()
                if len(body_preview) > 500:
                    body_preview = body_preview[:500] + "...(truncated)"
                msg = (
                    "Non-JSON response from API "
                    f"(status={response.status_code}, content-type={content_type or 'unknown'}): {body_preview}"
                )
                logger.error(msg)
                raise APIError(msg)

            body_text = (response.text or "").strip()
            if not body_text:
                msg = f"Empty response body from API [ReqID: {req_id}]"
                logger.error(msg)
                raise APIError(msg)

            try:
                return response.json()
            except ValueError:
                msg = f"Invalid JSON response from API [ReqID: {req_id}]"
                logger.error(msg)
                raise APIError(msg)
            
        except requests.exceptions.RequestException as e:
            # Masking sensitive URL parameters if any (though we use body mostly)
            safe_error = str(e).replace(settings.SORA_API_KEY, "******")
            logger.error(f"API Request Failed: {safe_error}")
            raise APIError(safe_error)

    @retry(
        retry=retry_if_exception_type((APIError, RateLimitError)), 
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def create_task(self, prompt: str, duration: int, resolution: str, is_pro: bool, image_url: Optional[str] = None, **kwargs) -> str:
        """
        Creates a video generation task.
        Returns task_id.
        """
        payload = {
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "is_pro": is_pro,
            "image_url": image_url,
            "remove_watermark": True,
            **kwargs
        }
        
        payload = {k: v for k, v in payload.items() if v is not None}
        
        # Log masked payload
        logger.debug(f"Creating task") 
        
        result = self._request("POST", "/create", payload)
        
        if result.get("code") != 200:
            raise APIError(f"API Error: {result.get('message')}")
            
        return result["data"]["task_id"]

    @retry(
        retry=retry_if_exception_type((APIError, RateLimitError)), 
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Gets task status.
        """
        result = self._request("GET", f"/tasks/{task_id}")
        
        if result.get("code") != 200:
            raise APIError(f"API Error: {result.get('message')}")
            
        return result["data"]
